-- shortcodes.lua: {{< wbtable >}} renders a snapped TSV as a table;
-- {{< wbref >}} links another entry by slug.

local C = dofile(quarto.utils.resolve_path("common.lua"))

local function kw(kwargs, key)
  local v = kwargs[key]
  if v == nil then return "" end
  return C.str(v)
end

local function trim(s) return (s:gsub("^%s+", ""):gsub("%s+$", "")) end

-- Lists are separated by '|' when one is present, otherwise by ','.
local function split_list(s)
  local out = {}
  if s == nil or s == "" then return out end
  local sep = s:find("|", 1, true) and "|" or ","
  for part in (s .. sep):gmatch("([^" .. (sep == "|" and "|" or ",") .. "]*)" .. (sep == "|" and "%|" or ",")) do
    table.insert(out, trim(part))
  end
  return out
end

local function is_number(s)
  if s == nil then return false end
  s = trim(s)
  return s:match("^[-+]?%d*%.?%d+[eE][-+]?%d+$") ~= nil or s:match("^[-+]?%d*%.?%d+$") ~= nil
end

-- Judge by value, not spelling: write.table writes 100000 as 1e+05.
local function is_decimal(s)
  if not is_number(s) then return false end
  local x = tonumber(s)
  return x ~= math.floor(x)
end

-- A number format must be a whole number of decimals, sN with N >= 1, or p.
local function valid_spec(spec)
  return spec:match("^%d+$") ~= nil or spec == "p" or (spec:match("^s%d+$") ~= nil and tonumber(spec:sub(2)) >= 1)
end

-- Format one numeric cell. spec: number of decimals (e.g. "3"), "sN" for N
-- significant figures, or "p" for p-values (3 decimals, "< 0.001" below).
local function fmt_cell(s, spec, decimal_col)
  if spec == nil or not is_number(s) then return s end
  local x = tonumber(s)
  if not decimal_col and s:match("[eE]") then return string.format("%.0f", x) end
  if spec == "p" then
    if x < 0.001 then return "< 0.001" end
    return string.format("%.3f", x)
  end
  local sig = spec:match("^s(%d+)$")
  if sig then
    sig = tonumber(sig)
    if x == 0 then return "0" end
    if not decimal_col and not is_decimal(s) then return s end
    local mag = math.floor(math.log(math.abs(x), 10))
    if mag < -4 or mag >= 6 then return string.format("%." .. (sig - 1) .. "e", x) end
    local d = math.max(0, sig - 1 - mag)
    return string.format("%." .. d .. "f", x)
  end
  local d = tonumber(spec)
  if not d then return s end
  if not decimal_col then return s end -- leave count columns alone
  if x ~= 0 and math.abs(x) < 0.5 * 10 ^ (-d) then
    return string.format("%." .. math.max(0, d - 1) .. "e", x)
  end
  return string.format("%." .. d .. "f", x)
end

local OPS = { "<=", ">=", "!=", "==", "=", "<", ">" }

local function parse_where(where)
  local conds = {}
  if where == "" then return conds end
  for part in (where .. "&"):gmatch("([^&]*)&") do
    part = trim(part)
    if part ~= "" then
      local found
      for _, op in ipairs(OPS) do
        local a, b = part:find(op, 1, true)
        if a then
          found = { col = trim(part:sub(1, a - 1)), op = op, val = trim(part:sub(b + 1)) }
          break
        end
      end
      if not found or found.col == "" then return nil, "cannot parse condition '" .. part .. "'" end
      table.insert(conds, found)
    end
  end
  return conds
end

local function test(cell, c)
  cell = cell or ""
  local op = c.op == "==" and "=" or c.op
  if is_number(cell) and is_number(c.val) then
    local x, y = tonumber(cell), tonumber(c.val)
    if op == "=" then return x == y end
    if op == "!=" then return x ~= y end
    if op == "<" then return x < y end
    if op == ">" then return x > y end
    if op == "<=" then return x <= y end
    if op == ">=" then return x >= y end
  end
  if op == "=" then return cell == c.val end
  if op == "!=" then return cell ~= c.val end
  return false
end

local function wbtable(args, kwargs)
  local rel = C.str(args[1])
  local doc = pandoc.path.filename(pandoc.path.directory(quarto.doc.input_file or "?"))
  local function fail(msg)
    return pandoc.Blocks({ pandoc.Para({ C.error_inline("wbtable " .. rel .. " in " .. doc .. ": " .. msg) }) })
  end
  if rel == "" then return fail("needs a path") end
  local path = pandoc.path.join({ pandoc.path.directory(quarto.doc.input_file), rel })
  local lines = C.read_lines(path)
  if not lines or #lines == 0 then return fail("cannot read the file") end

  local header = C.split_tab(lines[1])
  local pos = {}
  for i, h in ipairs(header) do pos[h] = i end
  local cols = split_list(kw(kwargs, "cols"))
  if #cols == 0 then cols = header end
  for _, c in ipairs(cols) do
    if not pos[c] then return fail("no column '" .. c .. "'") end
  end
  local labels = split_list(kw(kwargs, "labels"))
  if #labels > 0 and #labels ~= #cols then
    return fail(string.format("%d labels for %d columns (separate labels with '|' if they contain commas)", #labels, #cols))
  end

  -- Number formats: digits=N (decimals) or sig=N (significant figures) for
  -- every column, overridden per column by fmt="col=spec col=spec".
  local default_spec
  if kw(kwargs, "sig") ~= "" then default_spec = "s" .. kw(kwargs, "sig") end
  if kw(kwargs, "digits") ~= "" then default_spec = kw(kwargs, "digits") end
  local spec = {}
  for col, s in kw(kwargs, "fmt"):gmatch("([^%s=]+)=([^%s]+)") do
    if not pos[col] then return fail("fmt names unknown column '" .. col .. "'") end
    spec[col] = s
  end
  for _, c in ipairs(split_list(kw(kwargs, "pcols"))) do
    if not pos[c] then return fail("pcols names unknown column '" .. c .. "'") end
    spec[c] = "p"
  end
  if default_spec and not valid_spec(default_spec) then
    return fail("digits must be a whole number and sig a whole number of at least 1")
  end
  for col, s in pairs(spec) do
    if not valid_spec(s) then return fail("fmt for '" .. col .. "' must be N, sN or p, not '" .. s .. "'") end
  end

  local conds, err = parse_where(kw(kwargs, "where"))
  if not conds then return fail(err) end
  for _, c in ipairs(conds) do
    if not pos[c.col] then return fail("where names unknown column '" .. c.col .. "'") end
  end

  local max_rows = tonumber(kw(kwargs, "max-rows")) or 25
  local rows, total = {}, 0
  for i = 2, #lines do
    local r = C.split_tab(lines[i])
    local keep = true
    for _, c in ipairs(conds) do
      if not test(r[pos[c.col]], c) then keep = false break end
    end
    if keep then
      total = total + 1
      if #rows < max_rows then table.insert(rows, r) end
    end
  end
  if total == 0 then return fail("no rows match where=\"" .. kw(kwargs, "where") .. "\"") end

  local aligns, widths, head, decimal = {}, {}, {}, {}
  for j, c in ipairs(cols) do
    local numeric, dec = true, false
    for _, r in ipairs(rows) do
      local v = r[pos[c]] or ""
      if v ~= "" and v ~= "NA" then
        if not is_number(v) then numeric = false end
        if is_decimal(v) then dec = true end
      end
    end
    decimal[c] = dec
    aligns[j] = numeric and pandoc.AlignRight or pandoc.AlignLeft
    widths[j] = 0
    head[j] = { pandoc.Plain(pandoc.Inlines(labels[j] or c)) }
  end
  local body = {}
  for _, r in ipairs(rows) do
    local cells = {}
    for j, c in ipairs(cols) do
      cells[j] = { pandoc.Plain(pandoc.Inlines(fmt_cell(r[pos[c]] or "", spec[c] or default_spec, decimal[c]))) }
    end
    table.insert(body, cells)
  end
  local tbl = pandoc.utils.from_simple_table(pandoc.SimpleTable(pandoc.Inlines({}), aligns, widths, head, body))

  local note = pandoc.Inlines({})
  if total > #rows then
    note:extend(pandoc.Inlines(string.format("First %d of %d rows. ", #rows, total)))
  end
  note:insert(pandoc.Link(pandoc.Inlines("Full table (TSV)"), rel))
  -- Caption above, table in its own scroll region (focusable, so the keyboard can
  -- scroll it), source line below. Narrow tables do not stretch to the full width.
  local label = kw(kwargs, "caption")
  local parts = {}
  if label ~= "" then
    table.insert(parts, pandoc.Div({ pandoc.Para(pandoc.Inlines(label)) }, { class = "wb-table-caption" }))
  end
  table.insert(parts, pandoc.Div({ tbl }, { class = "wb-table-scroll", tabindex = "0", role = "region",
    ["aria-label"] = label ~= "" and label or ("Table from " .. rel) }))
  table.insert(parts, pandoc.Div({ pandoc.Plain(note) }, { class = "wb-table-source" }))
  return pandoc.Blocks({ pandoc.Div(parts, { class = "wb-table" .. (#cols <= 4 and " wb-table-narrow" or "") }) })
end

local function wbref(args)
  local slug = C.str(args[1])
  local text = args[2] and C.str(args[2]) or nil
  if slug == "" then return C.error_inline("wbref needs a slug") end
  return C.entry_link(slug, text)
end

-- ---------------------------------------------------------------- entry lists

local STATUS_ORDER = { current = 1, running = 2, planned = 3, superseded = 4, retracted = 5 }
local list_counter = 0
local FIELD_LABEL = {
  entry = "Entry", chapter = "Chapter", kind = "Kind", status = "Status", evidence = "Evidence",
  updated = "Updated", date = "Reported", answer = "Answer", question = "Question",
}

local function set_of(s)
  local out = {}
  for _, v in ipairs(split_list(s)) do out[v] = true end
  return next(out) and out or nil
end

local function entries_matching(kwargs)
  local idx = C.index()
  local status, kind = set_of(kw(kwargs, "status")), set_of(kw(kwargs, "kind"))
  local chapter = kw(kwargs, "chapter")
  if chapter == "this" then chapter = C.this_chapter() or "" end
  local out = {}
  for slug, e in pairs(idx.entries) do
    if (not status or status[e.status]) and (not kind or kind[e.kind]) and (chapter == "" or e.chapter == chapter) then
      e.slug = slug
      table.insert(out, e)
    end
  end
  local sort = kw(kwargs, "sort")
  if sort == "" then sort = "updated" end
  local function chord(e) local c = idx.chapters[e.chapter]; return c and tonumber(c.order) or 50 end
  table.sort(out, function(a, b)
    if sort == "date" then if a.date ~= b.date then return a.date < b.date end
    elseif sort == "title" then if a.title ~= b.title then return a.title:lower() < b.title:lower() end
    elseif sort == "chapter" then if chord(a) ~= chord(b) then return chord(a) < chord(b) end; if a.date ~= b.date then return a.date < b.date end
    elseif sort == "status" then
      local x, y = STATUS_ORDER[a.status] or 9, STATUS_ORDER[b.status] or 9
      if x ~= y then return x < y end
    else if a.updated ~= b.updated then return a.updated > b.updated end end
    return a.title:lower() < b.title:lower()
  end)
  local limit = tonumber(kw(kwargs, "limit"))
  if limit and #out > limit then
    local cut = {}
    for i = 1, limit do cut[i] = out[i] end
    out = cut
  end
  return out
end

local function status_pill(st)
  return '<span class="wb-pill wb-status wb-status-' .. C.esc(st) .. '">' .. C.esc(C.STATUS[st] or st) .. "</span>"
end

local function cell(field, e, idx)
  local off = C.offset()
  if field == "entry" then
    local q = (e.question and e.question ~= "") and ('<span class="wb-l-q">' .. C.esc(e.question) .. "</span>") or ""
    return '<a class="wb-l-title" href="' .. C.esc(off .. "/" .. e.href) .. '">' .. C.esc(e.title) .. "</a>" .. q
  elseif field == "chapter" then
    local c = idx.chapters[e.chapter]
    if not c then return C.esc(e.chapter) end
    return '<a href="' .. C.esc(off .. "/" .. c.href) .. '">' .. C.esc(c.title) .. "</a>"
  elseif field == "status" then
    return status_pill(e.status)
  elseif field == "kind" then
    return C.esc(C.KINDS[e.kind] or e.kind)
  elseif field == "evidence" then
    return (e.evidence and e.evidence ~= "") and C.esc(e.evidence) or '<span class="wb-l-none">–</span>'
  elseif field == "answer" then
    local a = e.answer or ""
    if a:match("^%s*[Pp]ending%.?%s*$") then return '<span class="wb-l-none">Not yet answered</span>' end
    return C.md_html(a)
  elseif field == "question" then
    return C.esc(e.question)
  else
    return C.esc(e[field] or "")
  end
end

local function wblist(args, kwargs)
  local idx = C.index()
  local list = entries_matching(kwargs)
  local fields = split_list(kw(kwargs, "fields"))
  if #fields == 0 then fields = { "entry", "status", "updated", "answer" } end
  local heading, hid = kw(kwargs, "heading"), kw(kwargs, "id")
  local empty = kw(kwargs, "empty")
  if #list == 0 then
    if heading ~= "" or empty == "none" then return pandoc.Blocks({}) end
    return pandoc.Blocks({ pandoc.RawBlock("html", '<p class="wb-list-empty">' .. C.esc(empty ~= "" and empty or "No entries yet.") .. "</p>") })
  end
  local filter = kw(kwargs, "filter") == "true"
  local h = {}
  if heading ~= "" then
    table.insert(h, '<h2 id="' .. C.esc(hid ~= "" and hid or heading:lower():gsub("%W+", "-")) .. '" class="anchored">' .. C.esc(heading) .. "</h2>")
  end
  table.insert(h, '<div class="wb-list"' .. (filter and " data-wb-filter" or "") .. ">")
  if filter then
    list_counter = list_counter + 1
    local fid = "wb-filter-" .. list_counter
    table.insert(h, '<div class="wb-list-tools"><label for="' .. fid .. '">Filter</label>' ..
      '<input id="' .. fid .. '" type="search" placeholder="Words in a title, question, chapter, status or tag" autocomplete="off">' ..
      '<span class="wb-list-count" aria-live="polite">' .. #list .. " entries</span></div>" ..
      '<p class="wb-list-tag" hidden>Showing entries tagged <strong class="wb-list-tag-name"></strong>. ' ..
      '<button type="button">Show all entries</button></p>')
  end
  table.insert(h, '<table class="wb-list-table"><thead><tr>')
  for _, f in ipairs(fields) do
    local label = FIELD_LABEL[f] or f
    if filter and f ~= "answer" and f ~= "question" then
      table.insert(h, '<th scope="col" class="wb-c-' .. f .. '" aria-sort="none"><button type="button" data-key="' .. f .. '">' .. label ..
        '<span class="wb-sort-ind" aria-hidden="true"></span></button></th>')
    else
      table.insert(h, '<th scope="col" class="wb-c-' .. f .. '">' .. label .. "</th>")
    end
  end
  table.insert(h, "</tr></thead><tbody>")
  for _, e in ipairs(list) do
    local c = idx.chapters[e.chapter]
    local search = table.concat({ e.title or "", e.question or "", e.answer or "", c and c.title or e.chapter or "",
      C.STATUS[e.status] or "", e.status or "", C.KINDS[e.kind] or "", e.evidence or "",
      table.concat(e.categories or {}, " ") }, " ")
    -- Tags as a JSON array, so a tag may contain any character.
    local tags = (e.categories and #e.categories > 0) and pandoc.json.encode(e.categories) or "[]"
    local corder = c and tonumber(c.order) or 50
    table.insert(h, string.format('<tr class="wb-row-%s" data-search="%s" data-tags="%s" data-entry="%s" data-status="%d" data-updated="%s" data-date="%s" data-chapter="%010.3f" data-kind="%s" data-evidence="%s">',
      C.esc(e.status), C.esc(search), C.esc(tags), C.esc((e.title or ""):lower()), STATUS_ORDER[e.status] or 9,
      C.esc(e.updated or ""), C.esc(e.date or ""), corder, C.esc(e.kind or ""), C.esc(e.evidence or "")))
    for _, f in ipairs(fields) do
      table.insert(h, '<td class="wb-c-' .. f .. '" data-label="' .. (FIELD_LABEL[f] or f) .. '">' .. cell(f, e, idx) .. "</td>")
    end
    table.insert(h, "</tr>")
  end
  table.insert(h, "</tbody></table></div>")
  return pandoc.Blocks({ pandoc.RawBlock("html", table.concat(h, "\n")) })
end

-- First sentence of a chapter's synthesis.
local function first_sentence(s)
  s = s or ""
  local cut = s:find("[%.%?!]%s+%u")
  return cut and s:sub(1, cut) or s
end

local function wbchapters()
  local idx = C.index()
  local rows = {}
  for id, c in pairs(idx.chapters) do
    c.id = id
    table.insert(rows, c)
  end
  table.sort(rows, function(a, b)
    local x, y = tonumber(a.order) or 50, tonumber(b.order) or 50
    if x ~= y then return x < y end
    return a.title < b.title
  end)
  local counts = {}
  for _, e in pairs(idx.entries) do
    counts[e.chapter] = counts[e.chapter] or {}
    counts[e.chapter][e.status] = (counts[e.chapter][e.status] or 0) + 1
  end
  local h = { '<div class="wb-list"><table class="wb-chapters"><thead><tr><th scope="col">Chapter</th><th scope="col">Contents</th></tr></thead><tbody>' }
  for _, c in ipairs(rows) do
    local parts = {}
    local base = C.offset() .. "/" .. c.href
    for _, st in ipairs({ "current", "running", "planned", "superseded", "retracted" }) do
      local n = (counts[c.id] or {})[st]
      if n then
        local anchor = (st == "superseded" or st == "retracted") and "#superseded" or "#entries"
        table.insert(parts, '<a class="wb-count wb-count-' .. st .. '" href="' .. C.esc(base .. anchor) .. '">' .. n .. " " .. C.esc((C.STATUS[st] or st):lower()) .. "</a>")
      end
    end
    local nb = math.floor(tonumber(c.backlog) or 0)
    if nb > 0 then
      table.insert(parts, '<a class="wb-count wb-count-backlog" href="' .. C.esc(base .. "#backlog") .. '">' .. nb .. " not yet added</a>")
    end
    local summary = first_sentence(c.summary)
    table.insert(h, '<tr><td class="wb-ch-name"><a href="' .. C.esc(C.offset() .. "/" .. c.href) .. '">' .. C.esc(c.title) .. "</a>" ..
      (summary ~= "" and ('<span class="wb-ch-sum">' .. C.md_html(summary) .. "</span>") or "") ..
      '</td><td class="wb-ch-counts" data-label="Contents">' .. (#parts > 0 and table.concat(parts, " ") or '<span class="wb-l-none">No entries yet</span>') .. "</td></tr>")
  end
  table.insert(h, "</tbody></table></div>")
  return pandoc.Blocks({ pandoc.RawBlock("html", table.concat(h, "\n")) })
end

-- A chapter's backlog: work that exists but has no entry yet (front matter
-- `backlog:` on the chapter page). Renders nothing when the backlog is empty.
local function wbbacklog(args, kwargs, meta)
  return C.backlog_blocks(meta)
end

-- Every chapter's backlog, counted, for the Open questions page.
local function wbbacklogs()
  local idx = C.index()
  local rows = {}
  for id, c in pairs(idx.chapters) do
    local n = math.floor(tonumber(c.backlog) or 0)
    if n > 0 then table.insert(rows, { c = c, n = n }) end
  end
  if #rows == 0 then
    return pandoc.Blocks({ pandoc.RawBlock("html", '<p class="wb-list-empty">Nothing is waiting to be added.</p>') })
  end
  table.sort(rows, function(a, b) return (tonumber(a.c.order) or 50) < (tonumber(b.c.order) or 50) end)
  local li = {}
  for _, r in ipairs(rows) do
    table.insert(li, { pandoc.Plain({ pandoc.Link(pandoc.Inlines(r.c.title), C.offset() .. "/" .. r.c.href .. "#backlog"),
      pandoc.Str(": " .. string.format("%d", r.n) .. (r.n == 1 and " item" or " items")) }) })
  end
  return pandoc.Blocks({ pandoc.BulletList(li) })
end

-- A getting-started panel, shown only while the workbook has no entries.
local function wbstart()
  local idx = C.index()
  if next(idx.entries) ~= nil then return pandoc.Blocks({}) end
  local html = [[
<div class="wb-start" role="note">
<p class="wb-start-title">This workbook has no entries yet.</p>
<p>Each analysis becomes one entry, grouped into chapters by research question. From the project folder:</p>
<ol>
<li>Add a chapter: <code>Rscript workbook/_tools/wb.R chapter &lt;id&gt; --title "&lt;Title&gt;"</code></li>
<li>Add an entry: <code>Rscript workbook/_tools/wb.R new &lt;chapter&gt; &lt;slug&gt; --title "&lt;Title&gt;"</code></li>
<li>Copy in its figures and tables with <code>wb.R snap</code>, write the entry, then run <code>wb.R build</code>.</li>
<li>Describe the project in a few sentences at the top of <code>workbook/index.qmd</code>.</li>
<li>Read the result served: <code>Rscript workbook/_tools/wb.R serve</code>, then open the address it prints.</li>
</ol>
<p>Agents follow the <code>workbook</code> skill, which describes every step.</p>
</div>]]
  return pandoc.Blocks({ pandoc.RawBlock("html", html) })
end

return {
  ["wbtable"] = wbtable,
  ["wbref"] = wbref,
  ["wblist"] = wblist,
  ["wbchapters"] = wbchapters,
  ["wbstart"] = wbstart,
  ["wbbacklog"] = wbbacklog,
  ["wbbacklogs"] = wbbacklogs,
}
