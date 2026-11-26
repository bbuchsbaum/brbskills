-- workbook.lua: renders the standard header, status banner, question-and-answer
-- panel and provenance block of every workbook entry from its front matter, so
-- every entry has the same anatomy. On every page it also adds the skip link and
-- the small script that makes tabsets, sidebar groups and entry lists usable by
-- keyboard, and marks template sections that have not been written yet.

local C = dofile(quarto.utils.resolve_path("common.lua"))

-- Labels for the answer panel, by status.
local ANSWER_LABEL = {
  current = "Answer", running = "Provisional answer", planned = "Answer",
  superseded = "Answer when superseded", retracted = "Retracted answer",
}

local function links(slugs)
  local out = {}
  for _, s in ipairs(slugs) do table.insert(out, C.entry_link(s)) end
  return C.join(out)
end

local function codes(paths)
  local out = {}
  for _, p in ipairs(paths) do
    if p:match("^https?://") then
      table.insert(out, pandoc.Link(pandoc.Inlines(p), p))
    else
      table.insert(out, C.path_code(p))
    end
  end
  return C.join(out)
end

local function meta_blocks(v)
  local t = pandoc.utils.type(v)
  if t == "Blocks" then return v end
  if t == "Inlines" then return pandoc.Blocks({ pandoc.Para(v) }) end
  return pandoc.Blocks({ pandoc.Para(pandoc.Inlines(C.str(v))) })
end

local function div(cls, blocks, attrs)
  local a = attrs or {}
  a.class = cls
  return pandoc.Div(blocks, a)
end

-- The most recent log line, without its date, for a retraction or supersession reason.
local function last_log(meta, pattern)
  local log = C.list(meta.log)
  for i = #log, 1, -1 do
    local line = log[i]
    if not pattern or line:lower():find(pattern) then
      local date, text = line:match("^(%d%d%d%d%-%d%d%-%d%d)%s*[%-—–]+%s*(.*)$")
      return date, text or line
    end
  end
end

local function banner(status, inlines)
  return div("wb-banner wb-banner-" .. status, { pandoc.Para(inlines) }, { role = "note" })
end

local function header_blocks(meta, slug)
  local kind = C.str(meta.kind)
  local status = C.str(meta.status)
  local evidence = C.str(meta.evidence)
  local date = C.str(meta.date)
  local updated = C.str(meta.updated)
  local idx = C.index()

  local line = pandoc.Inlines({})
  line:insert(C.pill("wb-status wb-status-" .. status, C.STATUS[status] or status))
  line:insert(pandoc.Space())
  line:insert(C.pill("wb-kind", C.KINDS[kind] or kind))
  if evidence ~= "" then
    line:insert(pandoc.Space())
    local ev = C.pill("wb-evidence wb-evidence-" .. evidence, evidence)
    ev.attributes.title = ({
      confirmatory = "The test was fixed before the outcome was seen.",
      exploratory = "Some choices were made after looking at the data.",
      descriptive = "No inferential test.",
    })[evidence] or ""
    line:insert(ev)
  end
  local dates = (kind == "plan" and "Written " or "Reported ") .. date
  if updated ~= "" and updated ~= date then dates = dates .. " · updated " .. updated end
  line:insert(pandoc.Space())
  line:insert(pandoc.Span(pandoc.Inlines(dates), { class = "wb-dates" }))
  local ch = C.str(meta.chapter)
  if ch ~= "" then
    line:insert(pandoc.Space())
    line:insert(pandoc.Span({ C.chapter_link(ch) }, { class = "wb-chapter" }))
  end

  local blocks = pandoc.Blocks({ div("wb-meta", { pandoc.Plain(line) }) })

  if status == "superseded" then
    local when, text = last_log(meta, "superseded")
    local p = pandoc.Inlines({ pandoc.Strong(pandoc.Inlines("Superseded")) })
    if when then p:extend(pandoc.Inlines(" on " .. when)) end
    p:extend(pandoc.Inlines(". Kept for the record; the question is now answered by "))
    p:extend(links(C.list(meta.superseded_by)))
    p:insert(pandoc.Str("."))
    -- A reason given with `wb supersede --reason` follows "Superseded by <slug>." in the log.
    local why = text and text:match("^[Ss]uperseded by [%w%-]+%.%s*(.+)$")
    if why and why ~= "" then
      p:insert(pandoc.Space())
      p:extend(pandoc.Inlines("Why: " .. why))
    end
    blocks:insert(banner("superseded", p))
  elseif status == "retracted" then
    local when, why = last_log(meta, "retract")
    local p = pandoc.Inlines({ pandoc.Strong(pandoc.Inlines("Retracted")) })
    if when then p:extend(pandoc.Inlines(" on " .. when)) end
    p:extend(pandoc.Inlines(". Do not rely on this result."))
    if why then why = why:gsub("^[Rr]etracted%s*[:%.;,%-—–]*%s*", "") end
    if why and why ~= "" then
      p:insert(pandoc.Space())
      p:extend(pandoc.Inlines("Why: " .. why:sub(1, 1):upper() .. why:sub(2)))
    end
    blocks:insert(banner("retracted", p))
  elseif status == "running" then
    blocks:insert(banner("running", pandoc.Inlines({ pandoc.Strong(pandoc.Inlines("In progress.")), pandoc.Space(),
      pandoc.Str("Results on this page are provisional and may change.") })))
  elseif status == "planned" then
    blocks:insert(banner("planned", pandoc.Inlines({ pandoc.Strong(pandoc.Inlines("Planned.")), pandoc.Space(),
      pandoc.Str("Nothing has been run yet; this page records the intention.") })))
  end

  if kind == "plan" then
    local executed = {}
    for _, b in ipairs(idx.backlinks[slug] or {}) do
      if b.rel == "executes" then table.insert(executed, b.slug) end
    end
    if #executed > 0 then
      local p = pandoc.Inlines({ pandoc.Strong(pandoc.Inlines("Executed")), pandoc.Str(" in ") })
      p:extend(links(executed))
      p:insert(pandoc.Str("."))
      blocks:insert(banner("current", p))
    end
  end

  -- Question and answer together: the part of the page a reader needs first.
  local qa = pandoc.Blocks({})
  if meta.question then
    local q = pandoc.utils.type(meta.question) == "Inlines" and meta.question or pandoc.Inlines(C.str(meta.question))
    qa:insert(div("wb-qa-label", { pandoc.Plain(pandoc.Inlines("Question")) }))
    qa:insert(div("wb-question", { pandoc.Para(q) }))
  end
  if meta.answer then
    local label = (kind == "analysis") and (ANSWER_LABEL[status] or "Answer") or "Summary"
    local ans = meta_blocks(meta.answer)
    if C.str(meta.answer):match("^%s*[Pp]ending%.?%s*$") then
      ans = pandoc.Blocks({ pandoc.Para(pandoc.Inlines(kind == "plan" and "Not yet run." or "Not yet answered.")) })
      qa:insert(div("wb-qa-label", { pandoc.Plain(pandoc.Inlines(label)) }))
      qa:insert(div("wb-answer wb-answer-pending", ans))
    else
      qa:insert(div("wb-qa-label", { pandoc.Plain(pandoc.Inlines(label)) }))
      qa:insert(div("wb-answer", ans))
    end
  end
  if #qa > 0 then
    blocks:insert(div("wb-qa wb-qa-" .. status, qa, { role = "region", ["aria-label"] = "Question and answer" }))
  end
  return blocks
end

local function provenance_blocks(meta, slug, tags)
  local idx = C.index()
  local items = {}
  local function add(term, inlines)
    if inlines and #inlines > 0 then
      table.insert(items, { pandoc.Inlines(term), { pandoc.Blocks({ pandoc.Plain(inlines) }) } })
    end
  end
  local function add_blocks(term, blocks)
    table.insert(items, { pandoc.Inlines(term), { blocks } })
  end

  add("Plan", links(C.list(meta.plan)))
  add("Shared methods", links(C.list(meta.methods)))
  add("Supersedes", links(C.list(meta.supersedes)))
  add("Superseded by", links(C.list(meta.superseded_by)))
  add("Related", links(C.list(meta.related)))
  add("Code", codes(C.list(meta.code)))
  add("Outputs", codes(C.list(meta.outputs)))
  add("Technical record", codes(C.list(meta.record)))
  local jobs = {}
  for _, j in ipairs(C.list(meta.jobs)) do table.insert(jobs, pandoc.Code(j)) end
  add("Cluster jobs", C.join(jobs))
  local v = C.str(meta.viewer)
  if v ~= "" then add("Interactive viewer", codes({ v })) end
  -- Tags link to the catalogue, filtered to that tag.
  local tag_inl = {}
  for _, t in ipairs(tags) do
    table.insert(tag_inl, pandoc.Link(pandoc.Inlines(t), C.offset() .. "/catalogue.html#tag=" .. C.urlencode(t),
      "Entries tagged " .. t, { class = "wb-tag" }))
  end
  add("Tags", C.join(tag_inl, ""))

  local man = C.read_lines(pandoc.path.join({ pandoc.path.directory(quarto.doc.input_file), "assets", "MANIFEST.tsv" }))
  if man and #man > 1 then
    local hdr = C.split_tab(man[1])
    local col = {}
    for i, h in ipairs(hdr) do col[h] = i end
    local rows = {}
    for i = 2, #man do
      local r = C.split_tab(man[i])
      local file, src, day = r[col.file], r[col.source], r[col.snapped]
      if file and file ~= "" then
        table.insert(rows, { pandoc.Plain({
          pandoc.Link({ pandoc.Code(file) }, "assets/" .. file), pandoc.Space(), pandoc.Str("←"), pandoc.Space(),
          C.path_code(src or "?"), pandoc.Space(), pandoc.Span(pandoc.Inlines("(" .. (day or "?") .. ")"), { class = "wb-nowrap" }),
        }) })
      end
    end
    if #rows > 0 then add_blocks("Snapshots", pandoc.Blocks({ pandoc.BulletList(rows) })) end
  end

  local back, seen = {}, {}
  for _, b in ipairs(idx.backlinks[slug] or {}) do
    if not seen[b.slug] and b.rel ~= "superseded" and b.rel ~= "supersedes" then
      seen[b.slug] = true
      table.insert(back, C.entry_link(b.slug))
    end
  end
  add("Referenced by", C.join(back))

  local hist = C.list(meta.log)
  if #hist > 0 then
    local rows = {}
    for _, h in ipairs(hist) do table.insert(rows, { pandoc.Plain(pandoc.Inlines(h)) }) end
    add_blocks("History", pandoc.Blocks({ pandoc.BulletList(rows) }))
  end

  if #items == 0 then return pandoc.Blocks({}) end
  return pandoc.Blocks({
    pandoc.Header(2, pandoc.Inlines("Provenance"), { id = "provenance" }),
    div("wb-provenance", { pandoc.DefinitionList(items) }),
  })
end

-- A level-2 section with nothing in it but template comments says so, rather
-- than showing a bare heading.
local function mark_empty_sections(blocks)
  local out = pandoc.Blocks({})
  local function is_blank(b)
    return b.t == "RawBlock" and b.text:match("^%s*<!%-%-.-%-%->%s*$") ~= nil
  end
  local n = #blocks
  for i, b in ipairs(blocks) do
    out:insert(b)
    if b.t == "Header" and b.level == 2 then
      local j = i + 1
      while j <= n and is_blank(blocks[j]) do j = j + 1 end
      if j > n or (blocks[j].t == "Header" and blocks[j].level <= 2) then
        out:insert(div("wb-unwritten", { pandoc.Para(pandoc.Inlines("Not written yet.")) }))
      end
    end
  end
  return out
end

-- The page script (workbook.js) is inlined, so it also runs when a page is
-- opened as a file. It adds the skip link itself, at the very start of the
-- page, so the link is the first Tab stop and stays out of the search index.
local function page_assets()
  local f = io.open(quarto.utils.resolve_path("workbook.js"), "r")
  if f then
    quarto.doc.include_text("after-body", "<script>\n" .. f:read("a") .. "\n</script>")
    f:close()
  end
end

function Pandoc(doc)
  if quarto.doc.is_format("html") then page_assets() end
  doc.blocks = mark_empty_sections(doc.blocks)
  -- A chapter page made before the backlog shortcode existed still shows its backlog.
  if doc.meta["wb-chapter"] then
    local f = io.open(quarto.doc.input_file or "", "r")
    local src = f and f:read("a") or ""
    if f then f:close() end
    if not src:find("wbbacklog", 1, true) then doc.blocks:extend(C.backlog_blocks(doc.meta)) end
  end
  local kind = C.str(doc.meta.kind)
  if C.KINDS[kind] == nil then return doc end
  -- Tags are shown in the provenance block and searched by the catalogue; the
  -- title-block chips Quarto would draw are removed so status leads the page.
  local tags = C.list(doc.meta.categories)
  doc.meta.categories = nil
  local input = quarto.doc.input_file or ""
  local slug = pandoc.path.filename(pandoc.path.directory(input))
  local blocks = pandoc.Blocks({})
  blocks:extend(header_blocks(doc.meta, slug))
  blocks:extend(doc.blocks)
  blocks:extend(provenance_blocks(doc.meta, slug, tags))
  doc.blocks = blocks
  return doc
end
