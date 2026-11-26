-- common.lua: helpers shared by the workbook filter and shortcodes.

local M = {}

M.KINDS = { analysis = "Analysis", data = "Data product", plan = "Plan", method = "Method", note = "Note" }
M.STATUS = {
  planned = "Planned", running = "In progress", current = "Current",
  superseded = "Superseded", retracted = "Retracted",
}

function M.str(v)
  if v == nil then return "" end
  local ok, s = pcall(pandoc.utils.stringify, v)
  if not ok or s == nil then return "" end
  return s
end

function M.list(v)
  local out = {}
  if v == nil then return out end
  local t = pandoc.utils.type(v)
  if t == "List" or t == "table" then
    for _, x in ipairs(v) do
      local s = M.str(x)
      if s ~= "" then table.insert(out, s) end
    end
  else
    local s = M.str(v)
    if s ~= "" then table.insert(out, s) end
  end
  return out
end

local cache
function M.index()
  if cache then return cache end
  cache = { entries = {}, backlinks = {}, chapters = {} }
  local dir = quarto.project.directory
  if not dir then return cache end
  local f = io.open(pandoc.path.join({ dir, "_wb", "index.json" }), "r")
  if f then
    local ok, data = pcall(pandoc.json.decode, f:read("a"))
    f:close()
    if ok and type(data) == "table" then
      cache = data
      cache.entries = cache.entries or {}
      cache.backlinks = cache.backlinks or {}
      cache.chapters = cache.chapters or {}
    end
  end
  return cache
end

function M.offset()
  local o = quarto.project.offset
  if o == nil or o == "" then return "." end
  return o
end

function M.pill(cls, text)
  return pandoc.Span({ pandoc.Str(text) }, { class = "wb-pill " .. cls })
end

function M.error_inline(msg)
  quarto.log.warning("workbook: " .. msg)
  return pandoc.Span({ pandoc.Str("[" .. msg .. "]") }, { class = "wb-error" })
end

-- Link to another entry by slug, with a status pill when it is not current.
function M.entry_link(slug, text)
  local e = M.index().entries[slug]
  if not e then return M.error_inline("unknown entry: " .. slug) end
  local label = (text and text ~= "") and text or e.title
  local inl = pandoc.Inlines({ pandoc.Link(pandoc.Inlines(label), M.offset() .. "/" .. e.href, e.title, { class = "wb-ref" }) })
  if e.status and e.status ~= "current" then
    inl:insert(pandoc.Space())
    inl:insert(M.pill("wb-status wb-status-" .. e.status, M.STATUS[e.status] or e.status))
  end
  return pandoc.Span(inl, { class = "wb-refwrap" })
end

function M.chapter_link(id)
  local c = M.index().chapters[id]
  if not c then return pandoc.Str(id) end
  return pandoc.Link(pandoc.Inlines(c.title), M.offset() .. "/" .. c.href)
end

function M.join(items, sep)
  local out = pandoc.Inlines({})
  for i, x in ipairs(items) do
    if i > 1 then
      out:insert(pandoc.Str(sep or ","))
      out:insert(pandoc.Space())
    end
    out:insert(x)
  end
  return out
end

function M.read_lines(path)
  local f = io.open(path, "r")
  if not f then return nil end
  local txt = f:read("a")
  f:close()
  local lines = {}
  for line in (txt .. "\n"):gmatch("([^\n]*)\n") do
    line = line:gsub("\r$", "")
    table.insert(lines, line)
  end
  while #lines > 0 and lines[#lines] == "" do table.remove(lines) end
  return lines
end

function M.esc(s)
  return (tostring(s or ""):gsub("[&<>\"]", { ["&"] = "&amp;", ["<"] = "&lt;", [">"] = "&gt;", ['"'] = "&quot;" }))
end

-- Answers and summaries may contain wbref shortcodes; outside a document they
-- would print literally, so turn them into Markdown links first.
function M.expand_refs(md)
  local idx = M.index()
  return (md:gsub("{{<%s*wbref%s+\"?([%w%-]+)\"?%s*\"?([^\">]*)\"?%s*>}}", function(slug, text)
    local e = idx.entries[slug]
    if not e then return text ~= "" and text or slug end
    local label = (text ~= "" and text) or e.title
    return "[" .. label .. "](" .. M.offset() .. "/" .. e.href .. ")"
  end))
end

-- Inline Markdown (one paragraph) to an HTML string.
function M.md_html(md)
  if md == nil or md == "" then return "" end
  local doc = pandoc.read(M.expand_refs(md), "markdown")
  local inl = pandoc.Inlines({})
  for i, b in ipairs(doc.blocks) do
    if i > 1 then inl:insert(pandoc.Space()) end
    if b.content and pandoc.utils.type(b.content) == "Inlines" then inl:extend(b.content) end
  end
  return pandoc.write(pandoc.Pandoc({ pandoc.Plain(inl) }), "html")
end

-- Percent-encode a string for use in a URL fragment.
function M.urlencode(s)
  return (tostring(s or ""):gsub("[^A-Za-z0-9%-%._~]", function(c) return string.format("%%%02X", string.byte(c)) end))
end

-- A file path as inline code that may break after each slash, never mid-name.
function M.path_code(p)
  -- An inline block: a path moves to the next line whole when it fits there,
  -- and breaks only after a slash when it is longer than a line.
  local html = '<span class="wb-path"><code>' .. M.esc(p):gsub("/", "/<wbr>") .. "</code></span>"
  return pandoc.RawInline("html", html)
end

-- Replace Code inlines that look like paths with breakable ones.
function M.breakable_paths(inlines)
  return pandoc.Inlines(inlines):walk({
    Code = function(c)
      if c.text:find("/") then return M.path_code(c.text) end
    end,
  })
end

-- A chapter's backlog section, from its `backlog:` front matter.
function M.backlog_blocks(meta)
  local raw = meta.backlog
  if raw == nil then return pandoc.Blocks({}) end
  -- A backlog written as a single string is one item.
  if pandoc.utils.type(raw) ~= "List" then raw = { raw } end
  if #raw == 0 or M.str(raw[1]) == "" then return pandoc.Blocks({}) end
  local items = {}
  for _, it in ipairs(raw) do
    local t = pandoc.utils.type(it)
    local inl = (t == "Inlines") and it or pandoc.Inlines(M.str(it))
    table.insert(items, { pandoc.Plain(M.breakable_paths(inl)) })
  end
  return pandoc.Blocks({
    pandoc.Header(2, pandoc.Inlines("Not yet in the workbook"), { id = "backlog" }),
    pandoc.Para(pandoc.Inlines("Work that exists but has no entry yet.")),
    pandoc.BulletList(items),
  })
end

-- Chapter id of the page being rendered, for chapter pages (analyses/<id>/index.qmd).
function M.this_chapter()
  local f = quarto.doc.input_file or ""
  return f:match("analyses/([^/]+)/index%.qmd$") or f:match("analyses/([^/]+)/[^/]+/index%.qmd$")
end

function M.split_tab(line)
  local out = {}
  for cell in (line .. "\t"):gmatch("([^\t]*)\t") do
    cell = cell:gsub('^"(.*)"$', "%1"):gsub('\\"', '"')
    table.insert(out, cell)
  end
  return out
end

return M
