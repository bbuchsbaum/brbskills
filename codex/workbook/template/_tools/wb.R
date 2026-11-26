#!/usr/bin/env Rscript
# wb.R: maintenance tool for an analysis workbook (a Quarto website).
#
# Run from anywhere: Rscript <workbook>/_tools/wb.R <command> [arguments]
#
#   ls                                   list chapters and entries
#   new <chapter> <slug> [--kind K] [--title T]
#                                        create an entry from _templates/<K>.qmd
#   chapter <id> --title T [--order N]   create a chapter page
#   snap <slug> <file>... [--as NAME]    copy study outputs into the entry's assets/
#   unsnap <slug> <asset>...             remove snapped assets and their manifest rows
#   supersede <old> <new> [--date D] [--reason T]
#                                        mark <old> superseded by <new>, both sides
#   index                                write _wb/index.json and _wb/sidebar.yml
#   check [--sources-only]               lint sources and the rendered site
#   build                                index, quarto render, check
#   serve [--port N]                     serve _site on http://127.0.0.1:N (default 4321)
#   init <dir> [--title T]               copy the template into <dir>
#   upgrade <dir> [--pages]              refresh _extensions, _tools, _templates in <dir>;
#                                        --pages also moves the home, utility and
#                                        chapter pages to the current templates,
#                                        keeping their project text
#
# Exit status is 1 when check finds errors.

WB_VERSION <- "0.2.0"

for (p in c("yaml", "jsonlite", "digest")) {
  if (!requireNamespace(p, quietly = TRUE)) {
    stop(sprintf("wb.R needs the R package '%s'", p), call. = FALSE)
  }
}

KINDS <- c("analysis", "data", "plan", "method", "note")
STATUSES <- c("planned", "running", "current", "superseded", "retracted")
EVIDENCE <- c("confirmatory", "exploratory", "descriptive")
LIVE <- c("current", "running", "planned")
REQUIRED_SECTIONS <- list(
  analysis = c("Approach", "Results", "Interpretation", "Caveats"),
  data = c("Contents", "How it was made", "How to use it", "Caveats"),
  plan = c("Rationale", "Design", "Analysis plan", "Decision rules"),
  method = c("Summary", "Details"),
  note = character()
)
REQUIRED_FIELDS <- c(
  "title", "question", "answer", "kind", "status",
  "date", "updated", "chapter"
)
REF_FIELDS <- c("supersedes", "superseded_by", "related", "plan", "methods")
DEFAULT_STATUS <- c(
  analysis = "running", data = "running", plan = "planned",
  method = "running", note = "running"
)

# ---------------------------------------------------------------- utilities

die <- function(...) {
  cat("wb: ", sprintf(...), "\n", sep = "", file = stderr())
  quit(status = 2, save = "no")
}

today <- function() format(Sys.Date(), "%Y-%m-%d")

vec <- function(x) {
  if (is.null(x)) {
    return(character())
  }
  v <- as.character(unlist(x, use.names = FALSE))
  v[!is.na(v) & nzchar(trimws(v))]
}

scalar <- function(x) {
  v <- vec(x)
  if (length(v)) v[1] else ""
}

script_path <- function() {
  a <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", a[grep("^--file=", a)])
  if (!length(f)) die("cannot locate wb.R; run it with Rscript")
  normalizePath(gsub("~+~", " ", f[1], fixed = TRUE)) # Rscript encodes spaces as ~+~
}

# A YAML double-quoted scalar.
yq <- function(s) paste0('"', gsub('(["\\\\])', "\\\\\\1", s), '"')

safe_name <- function(name) {
  identical(basename(name), name) && !grepl("^\\.", name) && !grepl("\\s", name)
}

TOOL <- script_path()
TOOL_HOME <- dirname(dirname(TOOL)) # the workbook (or template) that holds this copy

parse_args <- function(args) {
  pos <- character()
  flags <- list()
  i <- 1
  while (i <= length(args)) {
    a <- args[i]
    if (startsWith(a, "--")) {
      key <- substring(a, 3)
      if (i < length(args) && !startsWith(args[i + 1], "--")) {
        flags[[key]] <- args[i + 1]
        i <- i + 2
      } else {
        flags[[key]] <- TRUE
        i <- i + 1
      }
    } else {
      pos <- c(pos, a)
      i <- i + 1
    }
  }
  list(pos = pos, flags = flags)
}

find_root <- function(flag_root = NULL) {
  if (!is.null(flag_root)) {
    r <- normalizePath(flag_root, mustWork = TRUE)
    if (!file.exists(file.path(r, "_workbook.yml"))) {
      die("%s has no _workbook.yml", r)
    }
    return(r)
  }
  if (file.exists(file.path(TOOL_HOME, "_workbook.yml"))) {
    return(TOOL_HOME)
  }
  d <- normalizePath(getwd())
  repeat {
    if (file.exists(file.path(d, "_workbook.yml"))) {
      return(d)
    }
    if (file.exists(file.path(d, "workbook", "_workbook.yml"))) {
      return(file.path(d, "workbook"))
    }
    up <- dirname(d)
    if (up == d) break
    d <- up
  }
  die("no workbook found; pass --root <dir> or run init")
}

read_config <- function(root) {
  cfg <- yaml::read_yaml(file.path(root, "_workbook.yml"))
  if (isTRUE(cfg$template)) {
    die("this is the skill's template, not a workbook; run: Rscript %s init <dir>", TOOL)
  }
  sr <- path.expand(scalar(cfg$study_root))
  if (!nzchar(sr)) sr <- ".."
  cfg$study_root_abs <- normalizePath(if (startsWith(sr, "/")) sr else file.path(root, sr), mustWork = FALSE)
  lim <- cfg$limits
  if (is.null(lim)) lim <- list()
  cfg$limits <- utils::modifyList(
    list(title_chars = 40, answer_words = 70, approach_words = 250),
    lim
  )
  cfg
}

# Front matter: first line '---', closed by the next '---'.
read_doc <- function(path) {
  lines <- readLines(path, warn = FALSE, encoding = "UTF-8")
  if (!length(lines) || lines[1] != "---") {
    return(list(fm = list(), body = lines, lines = lines, fm_end = 0, error = "no front matter"))
  }
  close <- which(lines[-1] == "---")
  if (!length(close)) {
    return(list(fm = list(), body = lines, lines = lines, fm_end = 0, error = "unterminated front matter"))
  }
  end <- close[1] + 1
  txt <- if (end > 2) paste(lines[2:(end - 1)], collapse = "\n") else ""
  fm <- tryCatch(yaml::yaml.load(txt), error = function(e) structure(list(), err = conditionMessage(e)))
  err <- attr(fm, "err")
  if (is.null(fm)) fm <- list()
  if (is.null(err) && length(fm) && (!is.list(fm) || is.null(names(fm)))) {
    fm <- list()
    err <- "front matter is not a set of key: value fields"
  }
  body <- if (end < length(lines)) lines[(end + 1):length(lines)] else character()
  list(fm = fm, body = body, lines = lines, fm_end = end, error = err)
}

# Drop fenced code blocks so '#' comments are not mistaken for headings.
strip_fences <- function(body) {
  keep <- rep(TRUE, length(body))
  inside <- FALSE
  for (i in seq_along(body)) {
    if (grepl("^\\s*(```|~~~)", body[i])) {
      inside <- !inside
      keep[i] <- FALSE
    } else if (inside) {
      keep[i] <- FALSE
    }
  }
  body[keep]
}

h2_headings <- function(body) {
  b <- strip_fences(body)
  h <- b[grepl("^## ", b)]
  trimws(sub("\\s*\\{[^}]*\\}\\s*$", "", sub("^## ", "", h)))
}

section_text <- function(body, name) {
  b <- strip_fences(body)
  starts <- grep("^#{1,2} ", b)
  hit <- which(trimws(sub("\\s*\\{[^}]*\\}\\s*$", "", sub("^## ", "", b))) == name & grepl("^## ", b))
  if (!length(hit)) {
    return(character())
  }
  s <- hit[1]
  nxt <- starts[starts > s]
  e <- if (length(nxt)) nxt[1] - 1 else length(b)
  if (e <= s) character() else b[(s + 1):e]
}

strip_comments <- function(txt) {
  x <- paste(txt, collapse = "\n")
  x <- gsub("<!--.*?-->", "", x, perl = TRUE)
  x
}

word_count <- function(txt) {
  x <- strip_comments(txt)
  x <- gsub("\\{\\{<[^>]*>\\}\\}", " ", x)
  x <- gsub("!?\\[([^]]*)\\]\\([^)]*\\)", "\\1", x)
  x <- gsub("(^|\n)\\s*[-*+]\\s+", "\\1", x) # list markers
  x <- gsub("[`*_#>|:]", " ", x) # hyphenated words count once
  w <- strsplit(trimws(x), "\\s+")[[1]]
  sum(nzchar(w))
}

# A section has content if it has words, a figure, or a shortcode.
has_content <- function(txt) {
  x <- strip_comments(txt)
  word_count(txt) > 0 || grepl("!\\[", x) || grepl("\\{\\{<", x)
}

html_escape <- function(x) {
  x <- gsub("&", "&amp;", x, fixed = TRUE)
  x <- gsub("<", "&lt;", x, fixed = TRUE)
  gsub(">", "&gt;", x, fixed = TRUE)
}

rel <- function(path, root) {
  root <- sub("/+$", "", root)
  ifelse(startsWith(path, paste0(root, "/")), substring(path, nchar(root) + 2), path)
}

sha <- function(path) digest::digest(file = path, algo = "sha256")

# ---------------------------------------------------------------- scanning

scan <- function(root) {
  adir <- file.path(root, "analyses")
  files <- if (dir.exists(adir)) list.files(adir, pattern = "^index\\.qmd$", recursive = TRUE, full.names = TRUE) else character()
  chapters <- list()
  entries <- list()
  for (f in files) {
    r <- rel(f, root)
    parts <- strsplit(r, "/", fixed = TRUE)[[1]]
    d <- read_doc(f)
    if (length(parts) == 3) {
      id <- parts[2]
      chapters[[id]] <- list(
        id = id, path = r, file = f, doc = d,
        title = { t <- scalar(d$fm$title); if (nzchar(t)) t else id },
        order = suppressWarnings(as.numeric(scalar(d$fm$order)))
      )
    } else if (length(parts) == 4) {
      slug <- parts[3]
      entries[[length(entries) + 1]] <- list(
        slug = slug, chapter_dir = parts[2], path = r, file = f,
        dir = dirname(f), doc = d, fm = d$fm
      )
    }
  }
  for (id in names(chapters)) if (is.na(chapters[[id]]$order)) chapters[[id]]$order <- 50
  if (length(chapters)) {
    chapters <- chapters[order(vapply(chapters, function(c) c$order, 0), names(chapters))]
  }
  list(chapters = chapters, entries = entries)
}

entry_refs <- function(e) {
  out <- lapply(REF_FIELDS, function(k) vec(e$fm[[k]]))
  names(out) <- REF_FIELDS
  out
}

body_mentions <- function(e) {
  b <- strip_comments(strip_fences(e$doc$body))
  m <- regmatches(b, gregexpr("\\{\\{<\\s*wbref\\s+\"?([A-Za-z0-9-]+)", b, perl = TRUE))[[1]]
  unique(sub("^\\{\\{<\\s*wbref\\s+\"?", "", m))
}

# ---------------------------------------------------------------- index

cmd_index <- function(root, quiet = FALSE) {
  cfg <- read_config(root)
  s <- scan(root)
  dir.create(file.path(root, "_wb"), showWarnings = FALSE)
  ents <- list()
  back <- list()
  add_back <- function(target, from, relation) {
    back[[target]] <<- c(back[[target]], list(list(slug = from, rel = relation)))
  }
  for (e in s$entries) {
    fm <- e$fm
    refs <- entry_refs(e)
    ents[[e$slug]] <- list(
      title = scalar(fm$title),
      href = sub("\\.qmd$", ".html", e$path),
      chapter = e$chapter_dir,
      kind = scalar(fm$kind),
      status = scalar(fm$status),
      evidence = scalar(fm$evidence),
      date = scalar(fm$date),
      updated = scalar(fm$updated),
      question = scalar(fm$question),
      answer = scalar(fm$answer),
      categories = as.list(vec(fm$categories)),
      refs = lapply(refs, as.list)
    )
    rel_name <- c(
      supersedes = "superseded", superseded_by = "supersedes",
      related = "related", plan = "executes", methods = "uses"
    )
    for (k in REF_FIELDS) for (t in refs[[k]]) add_back(t, e$slug, rel_name[[k]])
    for (t in setdiff(body_mentions(e), unlist(refs))) add_back(t, e$slug, "mentions")
  }
  # A chapter's summary is the first paragraph under its first level-2 heading
  # (the synthesis), comments removed; it feeds the home page's chapter overview.
  # The first paragraph of the first section; failing that, the paragraph
  # before the first heading (as on the Shared methods page).
  chapter_summary <- function(c) {
    b <- strip_fences(c$doc$body)
    b <- trimws(strsplit(strip_comments(b), "\n", fixed = TRUE)[[1]])
    first_para <- function(x) {
      start <- which(nzchar(x) & !grepl("^(#|:::|\\{\\{<)", x))[1]
      if (is.na(start)) {
        return("")
      }
      end <- start
      while (end < length(x) && nzchar(x[end + 1]) && !grepl("^(#|:::)", x[end + 1])) end <- end + 1
      paste(x[start:end], collapse = " ")
    }
    h <- grep("^## ", b)
    if (!length(h)) {
      return(first_para(b))
    }
    nxt <- c(h[-1], length(b) + 1)[1]
    s <- first_para(b[seq_len(nxt - 1)][-seq_len(h[1])])
    if (!nzchar(s) && h[1] > 1) s <- first_para(b[seq_len(h[1] - 1)])
    s
  }
  chs <- lapply(s$chapters, function(c) {
    list(
      title = c$title, href = sub("\\.qmd$", ".html", c$path),
      order = c$order, summary = chapter_summary(c),
      backlog = length(vec(c$doc$fm$backlog))
    )
  })
  idx <- list(version = WB_VERSION, entries = ents, backlinks = back, chapters = chs)
  if (!length(ents)) idx$entries <- structure(list(), names = character())
  if (!length(back)) idx$backlinks <- structure(list(), names = character())
  if (!length(chs)) idx$chapters <- structure(list(), names = character())
  writeLines(
    jsonlite::toJSON(idx, auto_unbox = TRUE, pretty = TRUE, null = "null"),
    file.path(root, "_wb", "index.json")
  )

  # Sidebar: utility pages, then chapters in order; live entries by date,
  # superseded and retracted ones in a collapsed subsection.
  label <- function(e) {
    t <- html_escape(scalar(e$fm$title))
    st <- scalar(e$fm$status)
    words <- c(running = "in progress", planned = "planned", retracted = "retracted")
    if (st %in% names(words)) {
      t <- sprintf(
        '%s <span class="wb-dot wb-dot-%s" aria-hidden="true"></span><span class="visually-hidden"> (%s)</span>',
        t, st, words[[st]]
      )
    }
    t
  }
  top <- c("index.qmd", "catalogue.qmd", "open.qmd", "changes.qmd", "glossary.qmd", "about.qmd")
  top <- top[file.exists(file.path(root, top))]
  contents <- lapply(top, function(p) if (p == "index.qmd") list(href = p, text = "Home") else p)
  for (c in s$chapters) {
    es <- Filter(function(e) e$chapter_dir == c$id, s$entries)
    st <- vapply(es, function(e) scalar(e$fm$status), "")
    dt <- vapply(es, function(e) scalar(e$fm$date), "")
    tt <- vapply(es, function(e) scalar(e$fm$title), "")
    o <- order(dt, tt)
    es <- es[o]
    st <- st[o]
    live <- es[!(st %in% c("superseded", "retracted"))]
    dead <- es[st %in% c("superseded", "retracted")]
    items <- lapply(live, function(e) list(href = e$path, text = label(e)))
    if (length(dead)) {
      items <- c(items, list(list(
        section = sprintf(
          if (any(st == "retracted")) "Superseded or retracted (%d)" else "Superseded (%d)",
          length(dead)
        ),
        contents = lapply(dead, function(e) list(href = e$path, text = label(e)))
      )))
    }
    if (length(items)) {
      contents <- c(contents, list(list(section = html_escape(c$title), href = c$path, contents = items)))
    } else {
      contents <- c(contents, list(list(href = c$path, text = html_escape(c$title))))
    }
  }
  sb <- list(website = list(sidebar = list(
    style = "docked", search = TRUE, `collapse-level` = 2L, contents = contents
  )))
  yaml12_bool <- function(x) {
    r <- ifelse(x, "true", "false")
    class(r) <- "verbatim"
    r
  }
  writeLines(
    c(
      "# Generated by _tools/wb.R index. Do not edit; edit entries instead.",
      yaml::as.yaml(sb, handlers = list(logical = yaml12_bool))
    ),
    file.path(root, "_wb", "sidebar.yml")
  )
  if (!quiet) cat(sprintf("wb: indexed %d entries in %d chapters\n", length(s$entries), length(s$chapters)))
  invisible(s)
}

# ---------------------------------------------------------------- check

cmd_check <- function(root, sources_only = FALSE) {
  cfg <- read_config(root)
  s <- scan(root)
  issues <- data.frame(level = character(), where = character(), msg = character(), stringsAsFactors = FALSE)
  flag <- function(level, where, fmt, ...) {
    issues[nrow(issues) + 1, ] <<- list(level, where, sprintf(fmt, ...))
  }
  lim <- cfg$limits
  slugs <- vapply(s$entries, function(e) e$slug, "")
  dup <- unique(slugs[duplicated(slugs)])
  for (d in dup) flag("error", d, "slug used by more than one entry; slugs must be unique across chapters")
  by_slug <- stats::setNames(s$entries, slugs)
  chapter_ids <- names(s$chapters)
  study <- cfg$study_root_abs

  for (e in s$entries) {
    w <- e$path
    fm <- e$fm
    if (!is.null(e$doc$error)) {
      flag("error", w, "front matter: %s", e$doc$error)
      next
    }
    if (!grepl("^[a-z0-9]+(-[a-z0-9]+)*$", e$slug)) flag("error", w, "slug '%s' is not kebab-case", e$slug)
    if (!(e$chapter_dir %in% chapter_ids)) flag("error", w, "chapter folder '%s' has no index.qmd; run: wb chapter %s --title ...", e$chapter_dir, e$chapter_dir)
    for (k in REQUIRED_FIELDS) if (!nzchar(scalar(fm[[k]]))) flag("error", w, "missing front-matter field '%s'", k)
    kind <- scalar(fm$kind)
    status <- scalar(fm$status)
    if (nzchar(kind) && !(kind %in% KINDS)) flag("error", w, "kind '%s' is not one of: %s", kind, paste(KINDS, collapse = ", "))
    if (nzchar(status) && !(status %in% STATUSES)) flag("error", w, "status '%s' is not one of: %s", status, paste(STATUSES, collapse = ", "))
    ev <- scalar(fm$evidence)
    if (kind == "analysis" && status == "current" && !(ev %in% EVIDENCE)) {
      flag("error", w, "a current analysis needs evidence: %s", paste(EVIDENCE, collapse = " | "))
    } else if (nzchar(ev) && !(ev %in% EVIDENCE)) {
      flag("error", w, "evidence '%s' is not one of: %s", ev, paste(EVIDENCE, collapse = ", "))
    }
    ch <- scalar(fm$chapter)
    if (nzchar(ch) && ch != e$chapter_dir) flag("error", w, "chapter field '%s' does not match folder '%s'", ch, e$chapter_dir)
    for (k in c("date", "updated")) {
      v <- scalar(fm[[k]])
      if (nzchar(v) && !grepl("^\\d{4}-\\d{2}-\\d{2}$", v)) flag("error", w, "%s '%s' is not YYYY-MM-DD", k, v)
    }
    if (nzchar(scalar(fm$updated)) && scalar(fm$updated) < scalar(fm$date)) flag("error", w, "updated is earlier than date")
    if (nchar(scalar(fm$title)) > lim$title_chars) flag("warn", w, "title has %d characters (limit %d); it is the sidebar label", nchar(scalar(fm$title)), lim$title_chars)
    q <- scalar(fm$question)
    if (nzchar(q) && !grepl("\\?\\s*$", q)) flag("warn", w, "question does not end with '?'")
    aw <- word_count(scalar(fm$answer))
    if (aw > lim$answer_words) flag("warn", w, "answer has %d words (limit %d)", aw, lim$answer_words)
    if (status == "current" && grepl("^\\s*pending\\.?\\s*$", scalar(fm$answer), ignore.case = TRUE)) flag("error", w, "status is current but answer is still 'Pending'")

    # references
    refs <- entry_refs(e)
    for (k in REF_FIELDS) for (t in refs[[k]]) {
      if (!(t %in% slugs)) flag("error", w, "%s refers to unknown entry '%s'", k, t)
    }
    for (t in body_mentions(e)) if (!(t %in% slugs)) flag("error", w, "wbref to unknown entry '%s'", t)
    if (status == "superseded" && !length(refs$superseded_by)) flag("error", w, "status superseded needs superseded_by")
    if (status != "superseded" && length(refs$superseded_by)) flag("error", w, "superseded_by is set but status is '%s'", status)
    for (t in refs$superseded_by) if (t %in% slugs && !(e$slug %in% vec(by_slug[[t]]$fm$supersedes))) {
      flag("error", w, "'%s' does not list '%s' in supersedes; run: wb supersede %s %s", t, e$slug, e$slug, t)
    }
    for (t in refs$supersedes) if (t %in% slugs && !(e$slug %in% vec(by_slug[[t]]$fm$superseded_by))) {
      flag("error", w, "'%s' does not list '%s' in superseded_by; run: wb supersede %s %s", t, e$slug, t, e$slug)
    }
    for (t in refs$plan) if (t %in% slugs && scalar(by_slug[[t]]$fm$kind) != "plan") flag("warn", w, "plan '%s' is not a kind: plan entry", t)
    for (t in refs$methods) if (t %in% slugs && !(scalar(by_slug[[t]]$fm$kind) %in% c("method", "data"))) flag("warn", w, "methods '%s' is not a method or data entry", t)
    if (kind == "plan" && status %in% c("planned", "running")) {
      users <- Filter(function(x) e$slug %in% vec(x$fm$plan) && scalar(x$fm$status) == "current", s$entries)
      if (length(users)) flag("warn", w, "plan is still '%s' but %s executes it; set status: current", status, users[[1]]$slug)
    }

    # sections
    body <- e$doc$body
    bf <- strip_fences(body)
    if (any(grepl("^# ", bf))) flag("error", w, "body has a level-1 heading; the title comes from front matter")
    heads <- h2_headings(body)
    if ("Provenance" %in% heads) flag("error", w, "do not write a Provenance section; the filter renders it from front matter (use '## Notes' for extra detail)")
    req <- REQUIRED_SECTIONS[[kind]]
    if (!is.null(req) && length(req)) {
      missing <- setdiff(req, heads)
      if (length(missing)) flag("error", w, "missing section(s): %s", paste(sprintf("'## %s'", missing), collapse = ", "))
      pos <- match(req[req %in% heads], heads)
      if (is.unsorted(pos)) flag("error", w, "sections out of order; expected %s", paste(req, collapse = " > "))
      if (status == "current") {
        for (sec in intersect(req, heads)) {
          if (!has_content(section_text(body, sec))) flag("error", w, "section '%s' is empty but status is current", sec)
        }
      }
      if ("Approach" %in% heads) {
        aw <- word_count(section_text(body, "Approach"))
        if (aw > lim$approach_words) flag("warn", w, "Approach has %d words (limit %d); move detail to the technical record", aw, lim$approach_words)
      }
    }
    if (status == "current" && any(grepl("<!-- wb:", body, fixed = TRUE))) flag("warn", w, "template guidance comments remain; delete them once the section is written")

    # provenance paths
    for (k in c("code", "outputs", "record")) for (p in vec(fm[[k]])) {
      if (grepl("^https?://", p)) next
      if (grepl("^(/|~)", p)) {
        flag("error", w, "%s path '%s' is absolute; write it relative to study_root", k, p)
        next
      }
      if (!file.exists(file.path(study, p))) flag("warn", w, "%s path not found under study root: %s", k, p)
    }
    if (kind == "analysis" && status == "current" && !length(vec(fm$code))) flag("warn", w, "current analysis lists no code")

    # assets and snapshots
    btxt <- paste(body, collapse = "\n")
    links <- regmatches(btxt, gregexpr("\\]\\(([^)\\s]+)", btxt, perl = TRUE))[[1]]
    links <- sub("^\\]\\(", "", links)
    links <- links[!grepl("^(https?:|mailto:|#|data:)", links)]
    tbls <- regmatches(btxt, gregexpr("\\{\\{<\\s*wbtable\\s+(\"[^\"]+\"|[^\"\\s>]+)", btxt, perl = TRUE))[[1]]
    tbls <- gsub("\"", "", sub("^\\{\\{<\\s*wbtable\\s+", "", tbls))
    for (p in unique(c(links, tbls))) {
      p0 <- sub("[?#].*$", "", p)
      if (grepl("\\.(qmd|html)$", p0) || grepl("^/", p0)) {
        if (grepl("\\.(qmd|html)$", p0)) flag("warn", w, "link '%s': use {{< wbref slug >}} to link entries", p0)
        next
      }
      if (!startsWith(p0, "assets/")) {
        flag("error", w, "'%s' is outside the entry's assets/; snap it with: wb snap %s <file>", p0, e$slug)
      } else if (!file.exists(file.path(e$dir, p0))) {
        flag("error", w, "missing asset %s", p0)
      }
    }
    if (any(grepl("!\\[\\]\\(", body))) flag("warn", w, "figure without a caption")
    man <- file.path(e$dir, "assets", "MANIFEST.tsv")
    snapped <- character()
    if (file.exists(man)) {
      m <- utils::read.delim(man, colClasses = "character", quote = "")
      snapped <- m$file
      for (i in seq_len(nrow(m))) {
        a <- file.path(e$dir, "assets", m$file[i])
        if (!file.exists(a)) {
          flag("error", w, "manifest lists %s but the file is missing", m$file[i])
          next
        }
        if (sha(a) != m$sha256[i]) flag("warn", w, "assets/%s was edited after snapping; re-snap from the source instead", m$file[i])
        src <- file.path(study, m$source[i])
        if (!file.exists(src)) {
          flag("warn", w, "source of assets/%s no longer exists: %s", m$file[i], m$source[i])
        } else if (sha(src) != m$sha256[i]) {
          flag("warn", w, "STALE: %s changed after it was snapped on %s; re-snap and re-read the entry", m$source[i], m$snapped[i])
        }
      }
    }
    adir <- file.path(e$dir, "assets")
    if (dir.exists(adir)) {
      present <- setdiff(list.files(adir), "MANIFEST.tsv")
      for (p in setdiff(present, snapped)) flag("warn", w, "assets/%s was not added with wb snap, so it has no provenance", p)
      for (p in present[grepl("\\.(tsv|csv)$", present)]) {
        first <- readLines(file.path(adir, p), n = 1, warn = FALSE)
        if (!length(first)) {
          flag("warn", w, "assets/%s is empty", p)
          next
        }
        hdr <- gsub("\"", "", tolower(strsplit(first, "[\t,]")[[1]]))
        if (any(hdr %in% c("participant", "participant_id", "subject", "subject_id", "sub", "subj"))) {
          flag("warn", w, "assets/%s has a participant column; confirm it holds no individual records", p)
        }
      }
    }
    if (kind == "analysis" && status == "current" && !length(links) && !length(tbls)) flag("warn", w, "current analysis shows no figure, table or evidence link")
  }

  # chapters
  for (c in s$chapters) {
    if (!isTRUE(c$doc$fm[["wb-chapter"]])) flag("warn", c$path, "chapter page lacks 'wb-chapter: true'")
    ord <- scalar(c$doc$fm$order)
    if (nzchar(ord) && is.na(suppressWarnings(as.numeric(ord)))) flag("error", c$path, "order '%s' is not a number", ord)
  }

  # terms
  terms <- cfg$terms
  if (length(terms)) {
    for (e in s$entries) {
      txt <- paste(c(scalar(e$fm$title), scalar(e$fm$question), scalar(e$fm$answer), strip_fences(e$doc$body)), collapse = "\n")
      for (t in terms) for (bad in vec(t$avoid)) {
        if (grepl(paste0("\\b\\Q", bad, "\\E\\b"), txt, ignore.case = TRUE, perl = TRUE)) {
          flag("warn", e$path, "uses '%s'; the glossary term is '%s'", bad, scalar(t$use))
        }
      }
    }
  }

  # privacy: sources, text assets, rendered site
  pats <- vec(cfg$privacy$forbid)
  if (length(pats)) {
    src_files <- c(
      list.files(root, pattern = "\\.qmd$", full.names = TRUE),
      list.files(file.path(root, "analyses"), pattern = "\\.(qmd|tsv|csv|md|json|txt|svg|html|xml|yml|yaml)$", recursive = TRUE, full.names = TRUE)
    )
    site <- file.path(root, "_site")
    site_files <- if (!sources_only && dir.exists(site)) list.files(site, pattern = "\\.(html|json|tsv|csv|txt|md|svg|xml)$", recursive = TRUE, full.names = TRUE) else character()
    for (f in c(src_files, site_files)) {
      txt <- paste(readLines(f, warn = FALSE), collapse = "\n")
      for (p in pats) if (grepl(p, txt, perl = TRUE)) flag("error", rel(f, root), "matches privacy pattern '%s'", p)
    }
  }

  # rendered site
  site <- file.path(root, "_site")
  if (!sources_only) {
    if (!dir.exists(site)) {
      flag("warn", "_site", "not rendered yet; run: wb build")
    } else {
      newest_src <- max(file.mtime(c(
        list.files(root, pattern = "\\.(qmd|yml)$", full.names = TRUE),
        list.files(file.path(root, "analyses"), recursive = TRUE, full.names = TRUE)
      )), na.rm = TRUE)
      html <- list.files(site, pattern = "\\.html$", recursive = TRUE, full.names = TRUE)
      if (length(html) && max(file.mtime(html)) < newest_src) flag("warn", "_site", "older than the sources; run: wb build")
      for (f in html) {
        txt <- paste(readLines(f, warn = FALSE), collapse = "\n")
        if (grepl('class="wb-error"', txt, fixed = TRUE)) flag("error", rel(f, root), "page shows a workbook rendering error (search for 'wb-error')")
        txt <- gsub("(?s)<script\\b[^>]*>.*?</script>", "", txt, perl = TRUE)
        refs <- regmatches(txt, gregexpr("(href|src)=\"([^\"]+)\"", txt, perl = TRUE))[[1]]
        refs <- sub("^(href|src)=\"", "", sub("\"$", "", refs))
        refs <- refs[!grepl("^(https?:|mailto:|data:|javascript:|#|//|tel:)", refs) & !grepl("${", refs, fixed = TRUE)]
        refs <- unique(sub("[?#].*$", "", refs))
        refs <- refs[nzchar(refs)]
        for (r in refs) {
          target <- file.path(dirname(f), utils::URLdecode(r))
          if (!file.exists(target)) flag("error", rel(f, root), "broken link: %s", r)
        }
      }
    }
  }

  ne <- sum(issues$level == "error")
  nw <- sum(issues$level == "warn")
  if (nrow(issues)) {
    issues <- issues[order(issues$level != "error", issues$where), ]
    for (i in seq_len(nrow(issues))) {
      cat(sprintf("%-5s %s: %s\n", toupper(issues$level[i]), issues$where[i], issues$msg[i]))
    }
  }
  cat(sprintf("wb check: %d entries, %d errors, %d warnings\n", length(s$entries), ne, nw))
  invisible(ne)
}

# ---------------------------------------------------------------- editing helpers

fm_lines <- function(lines) {
  close <- which(lines[-1] == "---")[1] + 1
  list(start = 2, end = close - 1)
}

# Replace the value of a top-level key (and its continuation lines: indented
# lines or column-0 list items) with 'value', which may span several lines.
fm_set <- function(lines, key, value) {
  r <- fm_lines(lines)
  i <- grep(paste0("^", key, ":"), lines[r$start:r$end]) + r$start - 1
  new <- if (length(value) == 1 && !grepl("\n", value)) paste0(key, ": ", value) else c(paste0(key, ":"), value)
  if (length(i)) {
    j <- i[1] + 1
    while (j <= r$end && grepl("^(\\s+|- )", lines[j])) j <- j + 1
    lines <- c(lines[seq_len(i[1] - 1)], new, lines[j:length(lines)])
  } else {
    lines <- append(lines, new, after = r$end)
  }
  lines
}

# Append a dated line to the log, rewriting the log as a block list. A line
# already present is not added twice.
fm_add_history <- function(lines, note, date = today()) {
  d <- read_doc_lines(lines)
  items <- vec(d$fm$log)
  item <- paste0(date, " — ", note)
  if (!(item %in% items)) items <- c(items, item)
  fm_set(lines, "log", paste0("  - ", vapply(items, yq, "")))
}

read_doc_lines <- function(lines) {
  tmp <- tempfile(fileext = ".qmd")
  on.exit(unlink(tmp))
  writeLines(lines, tmp)
  read_doc(tmp)
}

flow <- function(v) if (length(v)) paste0("[", paste(v, collapse = ", "), "]") else "[]"

write_validated <- function(path, lines) {
  tmp <- tempfile(fileext = ".qmd")
  writeLines(lines, tmp)
  d <- read_doc(tmp)
  if (!is.null(d$error)) die("edit of %s would break its front matter (%s); file left unchanged", path, d$error)
  file.copy(tmp, path, overwrite = TRUE)
  invisible(d)
}

find_entry <- function(s, slug) {
  for (e in s$entries) if (e$slug == slug) {
    return(e)
  }
  die("no entry with slug '%s' (see: wb ls)", slug)
}

# ---------------------------------------------------------------- commands

cmd_ls <- function(root) {
  s <- scan(root)
  for (c in s$chapters) {
    cat(sprintf("\n%s  [%s]  %s\n", c$title, c$id, c$path))
    es <- Filter(function(e) e$chapter_dir == c$id, s$entries)
    if (!length(es)) cat("  (no entries)\n")
    dt <- vapply(es, function(e) scalar(e$fm$date), "")
    for (e in es[order(dt)]) {
      cat(sprintf(
        "  %-10s %-9s %s  %-34s %s\n", scalar(e$fm$status), scalar(e$fm$kind),
        scalar(e$fm$updated), e$slug, scalar(e$fm$title)
      ))
    }
  }
  orphans <- Filter(function(e) !(e$chapter_dir %in% names(s$chapters)), s$entries)
  for (e in orphans) cat(sprintf("  (no chapter page) %s\n", e$path))
  cat("\n")
}

cmd_new <- function(root, a) {
  if (length(a$pos) < 2) die("usage: wb new <chapter> <slug> [--kind analysis] [--title T]")
  ch <- a$pos[1]
  slug <- a$pos[2]
  kind <- if (is.null(a$flags$kind)) "analysis" else a$flags$kind
  if (!(kind %in% KINDS)) die("kind must be one of: %s", paste(KINDS, collapse = ", "))
  if (!grepl("^[a-z0-9]+(-[a-z0-9]+)*$", slug)) die("slug must be kebab-case: lower-case words joined by hyphens")
  s <- scan(root)
  if (!(ch %in% names(s$chapters))) die("no chapter '%s'; chapters: %s (or create one: wb chapter %s --title ...)", ch, paste(names(s$chapters), collapse = ", "), ch)
  if (slug %in% vapply(s$entries, function(e) e$slug, "")) die("slug '%s' already exists", slug)
  tpl <- file.path(root, "_templates", paste0(kind, ".qmd"))
  if (!file.exists(tpl)) die("missing template %s", tpl)
  title <- if (is.null(a$flags$title)) slug else a$flags$title
  txt <- readLines(tpl, warn = FALSE)
  txt <- gsub("\"{{title}}\"", yq(title), txt, fixed = TRUE)
  txt <- gsub("{{date}}", today(), txt, fixed = TRUE)
  txt <- gsub("{{chapter}}", ch, txt, fixed = TRUE)
  txt <- gsub("{{status}}", DEFAULT_STATUS[[kind]], txt, fixed = TRUE)
  d <- file.path(root, "analyses", ch, slug)
  dir.create(file.path(d, "assets"), recursive = TRUE)
  writeLines(txt, file.path(d, "index.qmd"))
  cat(sprintf("wb: created %s\n", rel(file.path(d, "index.qmd"), root)))
  cat("next: fill question and provenance fields, snap outputs (wb snap), write the sections, then wb build\n")
}

cmd_chapter <- function(root, a) {
  if (!length(a$pos) || is.null(a$flags$title)) die("usage: wb chapter <id> --title T [--order N]")
  id <- a$pos[1]
  if (!grepl("^[a-z0-9]+(-[a-z0-9]+)*$", id)) die("chapter id must be kebab-case")
  d <- file.path(root, "analyses", id)
  if (file.exists(file.path(d, "index.qmd"))) die("chapter '%s' already exists", id)
  order <- if (is.null(a$flags$order)) "50" else a$flags$order
  txt <- readLines(file.path(root, "_templates", "chapter.qmd"), warn = FALSE)
  if (!grepl("^[0-9]+$", order)) die("--order must be a whole number")
  txt <- gsub("\"{{title}}\"", yq(a$flags$title), txt, fixed = TRUE)
  txt <- gsub("{{order}}", order, txt, fixed = TRUE)
  txt <- gsub("{{date}}", today(), txt, fixed = TRUE)
  dir.create(d, recursive = TRUE, showWarnings = FALSE)
  writeLines(txt, file.path(d, "index.qmd"))
  cat(sprintf("wb: created chapter %s\n", rel(file.path(d, "index.qmd"), root)))
}

cmd_snap <- function(root, a) {
  if (length(a$pos) < 2) die("usage: wb snap <slug> <file>... [--as NAME]")
  cfg <- read_config(root)
  s <- scan(root)
  e <- find_entry(s, a$pos[1])
  files <- a$pos[-1]
  if (!is.null(a$flags$as) && length(files) != 1) die("--as works with one file at a time")
  adir <- file.path(e$dir, "assets")
  dir.create(adir, showWarnings = FALSE)
  man <- file.path(adir, "MANIFEST.tsv")
  m <- if (file.exists(man)) utils::read.delim(man, colClasses = "character", quote = "") else
    data.frame(file = character(), source = character(), sha256 = character(), snapped = character(), stringsAsFactors = FALSE)
  study <- normalizePath(cfg$study_root_abs)
  # Check every file before copying any, so a refusal leaves assets/ unchanged.
  plan <- list()
  for (f in files) {
    # Relative paths resolve against the study root first, then the current
    # directory. A study-relative path is recorded as given, so results folders
    # that are symlinks into other storage still count as inside the study.
    srcrel <- NULL
    if (!grepl("^(/|~)", f) && !grepl("(^|/)\\.\\.(/|$)", f) && file.exists(file.path(study, f))) {
      src <- file.path(study, f)
      srcrel <- sub("^\\./", "", f)
    } else {
      cands <- if (grepl("^(/|~)", f)) path.expand(f) else file.path(getwd(), f)
      if (!file.exists(cands)) die("no such file: %s (looked in %s and %s)", f, study, getwd())
      src <- normalizePath(cands)
      if (!startsWith(src, paste0(study, "/"))) die("%s is outside the study root %s", f, study)
      srcrel <- rel(src, study)
    }
    if (dir.exists(src)) die("%s is a directory; snap individual files, and link interactive viewers with the viewer field", f)
    name <- if (is.null(a$flags$as)) basename(src) else a$flags$as
    if (name == "MANIFEST.tsv") die("MANIFEST.tsv is a reserved name")
    if (!safe_name(name)) die("asset name '%s' must be a plain file name without spaces; choose one with --as", name)
    prev <- c(m$source[m$file == name], vapply(Filter(function(p) p$name == name, plan), function(p) p$srcrel, ""))
    if (length(prev) && any(prev != srcrel)) die("assets/%s would hold both %s and %s; give one another name with --as (nothing copied)", name, prev[prev != srcrel][1], srcrel)
    size <- file.info(src)$size
    if (size > 5e6) die("%s is %.1f MB; workbook assets should be headline figures and tables, not bulk outputs", f, size / 1e6)
    plan[[length(plan) + 1]] <- list(src = src, srcrel = srcrel, name = name)
  }
  for (p in plan) {
    if (!file.copy(p$src, file.path(adir, p$name), overwrite = TRUE)) die("could not copy %s", p$src)
    row <- data.frame(file = p$name, source = p$srcrel, sha256 = sha(p$src), snapped = today(), stringsAsFactors = FALSE)
    m <- rbind(m[m$file != p$name, , drop = FALSE], row)
    cat(sprintf("wb: assets/%s <- %s\n", p$name, row$source))
  }
  utils::write.table(m, man, sep = "\t", quote = FALSE, row.names = FALSE)
}

cmd_unsnap <- function(root, a) {
  if (length(a$pos) < 2) die("usage: wb unsnap <slug> <asset-name>...")
  s <- scan(root)
  e <- find_entry(s, a$pos[1])
  adir <- file.path(e$dir, "assets")
  man <- file.path(adir, "MANIFEST.tsv")
  m <- if (file.exists(man)) utils::read.delim(man, colClasses = "character", quote = "") else NULL
  for (name in a$pos[-1]) {
    name <- sub("^assets/", "", name)
    if (!identical(basename(name), name) || name == "MANIFEST.tsv") die("'%s' is not an asset name", name)
    p <- file.path(adir, name)
    if (!file.exists(p)) die("no asset %s in %s", name, e$slug)
    file.remove(p)
    if (!is.null(m)) m <- m[m$file != name, , drop = FALSE]
    cat(sprintf("wb: removed assets/%s\n", name))
  }
  if (!is.null(m)) utils::write.table(m, man, sep = "\t", quote = FALSE, row.names = FALSE)
}

cmd_supersede <- function(root, a) {
  if (length(a$pos) != 2) die("usage: wb supersede <old> <new> [--date YYYY-MM-DD] [--reason TEXT]")
  when <- if (is.null(a$flags$date)) today() else a$flags$date
  if (!grepl("^\\d{4}-\\d{2}-\\d{2}$", when)) die("--date must be YYYY-MM-DD")
  s <- scan(root)
  old <- find_entry(s, a$pos[1])
  new <- find_entry(s, a$pos[2])
  if (old$slug == new$slug) die("an entry cannot supersede itself")
  lo <- old$doc$lines
  lo <- fm_set(lo, "status", "superseded")
  lo <- fm_set(lo, "superseded_by", flow(unique(c(vec(old$fm$superseded_by), new$slug))))
  if (when > scalar(old$fm$updated)) lo <- fm_set(lo, "updated", when)
  why <- if (is.null(a$flags$reason) || isTRUE(a$flags$reason)) "" else paste0(" ", sub("\\.?$", ".", a$flags$reason))
  lo <- fm_add_history(lo, sprintf("Superseded by %s.%s", new$slug, why), when)
  ln <- new$doc$lines
  ln <- fm_set(ln, "supersedes", flow(unique(c(vec(new$fm$supersedes), old$slug))))
  ln <- fm_add_history(ln, sprintf("Supersedes %s.", old$slug), when)
  # Validate both edits before writing either, so a failure leaves both files untouched.
  for (x in list(list(old$file, lo), list(new$file, ln))) {
    d <- read_doc_lines(x[[2]])
    if (!is.null(d$error)) die("edit of %s would break its front matter (%s); nothing changed", x[[1]], d$error)
  }
  write_validated(old$file, lo)
  write_validated(new$file, ln)
  cat(sprintf("wb: %s is now superseded by %s\n", old$slug, new$slug))
}

copy_tree <- function(from, to, overwrite) {
  files <- list.files(from, recursive = TRUE, all.files = TRUE, no.. = TRUE)
  changed <- character()
  for (f in files) {
    dst <- file.path(to, f)
    dir.create(dirname(dst), recursive = TRUE, showWarnings = FALSE)
    if (file.exists(dst) && !overwrite) next
    if (file.exists(dst) && sha(dst) == sha(file.path(from, f))) next
    file.copy(file.path(from, f), dst, overwrite = TRUE)
    changed <- c(changed, f)
  }
  changed
}

cmd_init <- function(a) {
  if (!length(a$pos)) die("usage: wb init <dir> [--title T]")
  dst <- a$pos[1]
  if (dir.exists(dst) && length(list.files(dst, all.files = TRUE, no.. = TRUE))) die("%s exists and is not empty", dst)
  dir.create(dst, recursive = TRUE, showWarnings = FALSE)
  copy_tree(TOOL_HOME, dst, overwrite = FALSE)
  title <- if (is.null(a$flags$title)) "Analysis workbook" else a$flags$title
  for (f in c("_workbook.yml", "_quarto.yml", "index.qmd")) {
    p <- file.path(dst, f)
    txt <- readLines(p, warn = FALSE)
    txt <- gsub("\"{{WB_TITLE}}\"", yq(title), txt, fixed = TRUE)
    txt <- gsub("{{date}}", today(), txt, fixed = TRUE)
    txt <- txt[!grepl("^template: true", txt)]
    writeLines(txt, p)
  }
  for (f in list.files(file.path(dst, "analyses"), pattern = "\\.qmd$", recursive = TRUE, full.names = TRUE)) {
    txt <- gsub("{{date}}", today(), readLines(f, warn = FALSE), fixed = TRUE)
    writeLines(txt, f)
  }
  cat(sprintf("wb: workbook created at %s\nnext: edit _workbook.yml (study_root, privacy), add chapters (wb chapter), then wb build\n", normalizePath(dst)))
}

cmd_upgrade <- function(a) {
  if (!length(a$pos)) die("usage: wb upgrade <dir>")
  dst <- normalizePath(a$pos[1], mustWork = TRUE)
  if (!file.exists(file.path(dst, "_workbook.yml"))) die("%s is not a workbook", dst)
  if (dst == TOOL_HOME) die("run upgrade from the skill's copy of wb.R")
  ch <- character()
  for (d in c("_extensions", "_tools", "_templates")) {
    ch <- c(ch, file.path(d, copy_tree(file.path(TOOL_HOME, d), file.path(dst, d), overwrite = TRUE)))
  }
  # Add top-level pages that newer versions introduced; never overwrite existing ones.
  for (p in list.files(TOOL_HOME, pattern = "\\.qmd$")) {
    if (!file.exists(file.path(dst, p))) {
      file.copy(file.path(TOOL_HOME, p), file.path(dst, p))
      ch <- c(ch, p)
    }
  }
  if (isTRUE(a$flags$pages)) ch <- c(ch, migrate_pages(dst))
  if (length(ch)) cat("wb: updated\n", paste0("  ", ch, "\n"), sep = "") else cat("wb: already up to date\n")
}

# Move a workbook's structural pages to the current templates. Kept: the home
# page's opening paragraphs and "Where things stand"; each chapter's title,
# order, backlog and synthesis. Replaced: catalogue, open questions, recent
# changes, about, and the Shared methods page, which hold no project text.
migrate_pages <- function(dst) {
  done <- character()
  fm_end <- function(l) which(l == "---")[2]
  is_guide <- function(x) grepl("^\\s*<!-- wb:.*-->\\s*$", x)
  trim_blank <- function(s) {
    while (length(s) && !nzchar(trimws(s[1]))) s <- s[-1]
    while (length(s) && !nzchar(trimws(s[length(s)]))) s <- s[-length(s)]
    s
  }
  section <- function(l, heading) {
    i <- which(sub("\\s*\\{[^}]*\\}\\s*$", "", l) == heading)
    if (!length(i)) {
      return(character())
    }
    nxt <- grep("^## ", l)
    nxt <- nxt[nxt > i[1]]
    e <- if (length(nxt)) nxt[1] - 1 else length(l)
    if (e <= i[1]) {
      return(character())
    }
    s <- l[(i[1] + 1):e]
    trim_blank(s[!is_guide(s)])
  }
  put <- function(l, marker, text) {
    if (!length(text)) {
      return(l)
    }
    i <- grep(marker, l, fixed = TRUE)
    if (length(i) != 1) {
      return(l)
    }
    c(l[seq_len(i - 1)], text, l[(i + 1):length(l)])
  }
  title_of <- function(l) sub('^title: *"?(.*?)"?\\s*$', "\\1", grep("^title:", l, value = TRUE)[1])
  for (p in c("catalogue.qmd", "open.qmd", "changes.qmd", "about.qmd")) {
    if (file.copy(file.path(TOOL_HOME, p), file.path(dst, p), overwrite = TRUE)) done <- c(done, p)
  }
  mp <- file.path("analyses", "methods", "index.qmd")
  if (file.exists(file.path(dst, mp))) {
    old <- readLines(file.path(dst, mp), warn = FALSE)
    new <- readLines(file.path(TOOL_HOME, mp), warn = FALSE)
    bi <- grep("^backlog:", old[seq_len(fm_end(old))])
    if (length(bi)) {
      j <- bi[1]
      while (j + 1 < fm_end(old) && grepl("^\\s+-", old[j + 1])) j <- j + 1
      new <- put(new, "backlog: []", old[bi[1]:j])
    }
    writeLines(new, file.path(dst, mp))
    done <- c(done, mp)
  }
  # Home page.
  hp <- file.path(dst, "index.qmd")
  if (file.exists(hp)) {
    old <- readLines(hp, warn = FALSE)
    body <- old[(fm_end(old) + 1):length(old)]
    h1 <- grep("^## ", body)[1]
    glance <- if (is.na(h1)) body else body[seq_len(h1 - 1)]
    glance <- trim_blank(glance[!is_guide(glance) & !grepl("^\\{\\{<", glance)])
    stand <- section(body, "## Where things stand")
    new <- readLines(file.path(TOOL_HOME, "index.qmd"), warn = FALSE)
    new <- sub("\"{{WB_TITLE}}\"", yq(title_of(old)), new, fixed = TRUE)
    new <- put(new, "<!-- wb: The study at a glance", glance)
    new <- put(new, "<!-- wb: The current synthesis across chapters", stand)
    writeLines(new, hp)
    done <- c(done, "index.qmd")
  }
  # Chapter pages.
  tpl <- readLines(file.path(dst, "_templates", "chapter.qmd"), warn = FALSE)
  for (d in list.dirs(file.path(dst, "analyses"), recursive = FALSE)) {
    f <- file.path(d, "index.qmd")
    if (basename(d) == "methods" || !file.exists(f)) next
    l <- readLines(f, warn = FALSE)
    fe <- fm_end(l)
    order <- sub("^order: *", "", grep("^order:", l[seq_len(fe)], value = TRUE)[1])
    if (is.na(order)) order <- "50"
    bi <- grep("^backlog:", l[seq_len(fe)])
    backlog <- character()
    if (length(bi)) {
      j <- bi[1]
      while (j + 1 < fe && grepl("^\\s+-", l[j + 1])) j <- j + 1
      backlog <- l[bi[1]:j]
    }
    syn <- section(l, "## Where this line of work stands")
    new <- sub("\"{{title}}\"", yq(title_of(l)), tpl, fixed = TRUE)
    new <- sub("{{order}}", order, new, fixed = TRUE)
    if (length(backlog)) new <- put(new, "backlog: []", backlog)
    new <- put(new, "<!-- wb: Two to five sentences", syn)
    writeLines(new, f)
    done <- c(done, file.path("analyses", basename(d), "index.qmd"))
  }
  done
}

# Serve the rendered site locally. Opening the HTML files directly (file://)
# disables search, the contents highlight and theme memory, so read it served.
cmd_serve <- function(root, a) {
  site <- file.path(root, "_site")
  if (!dir.exists(site)) die("no _site yet; run: wb build")
  port <- if (is.null(a$flags$port)) "4321" else a$flags$port
  if (!grepl("^[0-9]+$", port)) die("--port must be a number")
  py <- Sys.which("python3")
  if (!nzchar(py)) die("python3 is not on PATH; alternatively run: quarto preview %s", root)
  cat(sprintf("wb: serving %s at http://127.0.0.1:%s/ (Ctrl-C to stop)\n", site, port))
  invisible(system2(py, c("-m", "http.server", port, "--bind", "127.0.0.1", "--directory", shQuote(site))))
}

cmd_build <- function(root) {
  cmd_index(root)
  quarto <- Sys.which("quarto")
  if (!nzchar(quarto)) die("quarto is not on PATH")
  out <- suppressWarnings(system2(quarto, c("render", shQuote(root)), stdout = TRUE, stderr = TRUE))
  status <- attr(out, "status")
  warn <- grep("WARN|ERROR|workbook:", out, value = TRUE)
  # Chapters with no entries yet make Quarto warn about an empty listing; harmless.
  warn <- warn[!grepl("The listing in .* using the following contents", warn)]
  if (length(warn)) cat(gsub("\033\\[[0-9;]*m", "", warn), sep = "\n")
  if (!is.null(status) && status != 0) {
    cat(gsub("\033\\[[0-9;]*m", "", utils::tail(out, 40)), sep = "\n")
    cat("wb: quarto render failed\n")
    return(invisible(1))
  }
  cat(sprintf("wb: rendered %s\n", file.path(root, "_site", "index.html")))
  cmd_check(root)
}

# ---------------------------------------------------------------- main

main <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  if (!length(args) || args[1] %in% c("-h", "--help", "help")) {
    h <- readLines(TOOL)
    cat(sub("^# ?", "", h[3:grep("^# Exit status", h)[1]]), sep = "\n")
    return(invisible(0))
  }
  cmd <- args[1]
  a <- parse_args(args[-1])
  if (cmd == "init") {
    return(cmd_init(a))
  }
  if (cmd == "upgrade") {
    return(cmd_upgrade(a))
  }
  root <- find_root(a$flags$root)
  read_config(root)
  switch(cmd,
    ls = cmd_ls(root),
    new = cmd_new(root, a),
    chapter = cmd_chapter(root, a),
    snap = cmd_snap(root, a),
    unsnap = cmd_unsnap(root, a),
    supersede = cmd_supersede(root, a),
    index = cmd_index(root),
    check = {
      ne <- cmd_check(root, sources_only = isTRUE(a$flags[["sources-only"]]))
      if (ne > 0) quit(status = 1, save = "no")
    },
    serve = cmd_serve(root, a),
    build = {
      ne <- cmd_build(root)
      if (ne > 0) quit(status = 1, save = "no")
    },
    die("unknown command '%s' (try: wb.R help)", cmd)
  )
  invisible(0)
}

main()
