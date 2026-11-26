// workbook.js: inlined on every workbook page by the workbook filter, so it
// also runs when a page is opened as a file. It adds the skip link; keyboard
// access for tabsets, collapsible sidebar groups, the phone menu and the theme
// toggle; landmark and search names; breadcrumb pruning; scroll cues for wide
// tables; and filtering and sorting of entry lists.
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState === "loading")
      document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  // Case- and accent-insensitive text for matching.
  function fold(s) {
    s = String(s || "").toLowerCase();
    return s.normalize ? s.normalize("NFD").replace(/[̀-ͯ]/g, "") : s;
  }

  // Decode a URL fragment value; a lone "%" (already decoded by the site) is kept.
  function decode(s) {
    try {
      return decodeURIComponent(s);
    } catch (e) {
      try {
        return decodeURIComponent(s.replace(/%(?![0-9A-Fa-f]{2})/g, "%25"));
      } catch (e2) {
        return s;
      }
    }
  }

  // Path of a URL without a trailing index.html, for comparing pages.
  function pagePath(href) {
    try {
      return new URL(href, location.href).pathname.replace(/index\.html$/, "");
    } catch (e) {
      return href;
    }
  }

  ready(function () {
    // Skip link: the first Tab stop on every page; it moves focus to the content.
    var main = document.getElementById("quarto-document-content");
    if (main && !document.querySelector(".wb-skip")) {
      var skip = document.createElement("a");
      skip.className = "wb-skip";
      skip.href = "#quarto-document-content";
      skip.textContent = "Skip to content";
      skip.addEventListener("click", function (ev) {
        ev.preventDefault();
        main.setAttribute("tabindex", "-1");
        main.focus();
        main.scrollIntoView();
      });
      document.body.insertBefore(skip, document.body.firstChild);
    }

    // Breadcrumbs: keep chapter pages and the last crumb (this page). Drop
    // sidebar group labels, links back to this page, and links to other entries.
    var here = pagePath(location.href);
    document
      .querySelectorAll(".quarto-page-breadcrumbs .breadcrumb")
      .forEach(function (ol) {
        var items = Array.prototype.slice.call(
          ol.querySelectorAll(".breadcrumb-item"),
        );
        items.slice(0, -1).forEach(function (li) {
          var a = li.querySelector("a");
          var href = a && a.getAttribute("href");
          var path = href ? pagePath(href) : "";
          var isEntry = /\/analyses\/[^/]+\/[^/]+\/$/.test(path);
          if (!href || path === here || isEntry) li.remove();
        });
      });

    // Wide data tables: when a table is wider than its column, show a shadow
    // at the right edge and a line saying so. The line is created here, not in
    // the page, so it never reaches the search index.
    function markScrolls() {
      document.querySelectorAll(".wb-table-scroll").forEach(function (box) {
        var table = box.closest(".wb-table");
        if (!table) return;
        var wide = box.scrollWidth > box.clientWidth + 1;
        table.classList.toggle("wb-scrolls", wide);
        var hint = table.querySelector(".wb-scroll-hint");
        if (wide && !hint) {
          var src = table.querySelector(".wb-table-source p, .wb-table-source");
          if (src) {
            hint = document.createElement("span");
            hint.className = "wb-scroll-hint";
            hint.textContent = " Scroll sideways for more columns.";
            src.appendChild(hint);
          }
        }
        if (hint) hint.hidden = !wide;
      });
    }
    markScrolls();
    window.addEventListener("resize", markScrolls);
    document.addEventListener("shown.bs.tab", markScrolls);

    // Tabsets: Quarto's tab links have no href, so they cannot take focus.
    // An href to their pane makes the active tab focusable; Bootstrap's tab
    // plugin then moves between tabs with the arrow keys.
    document
      .querySelectorAll('[role="tab"][aria-controls]')
      .forEach(function (tab) {
        if (!tab.getAttribute("href"))
          tab.setAttribute("href", "#" + tab.getAttribute("aria-controls"));
      });

    // Collapsible sidebar groups without a page of their own are links with no
    // href: make them buttons that Enter and Space operate.
    function asButton(el, name) {
      el.setAttribute("role", "button");
      if (!el.hasAttribute("tabindex")) el.setAttribute("tabindex", "0");
      if (name) el.setAttribute("aria-label", name);
      el.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          el.click();
        }
      });
    }
    document
      .querySelectorAll('#quarto-sidebar a[data-bs-toggle="collapse"]')
      .forEach(function (a) {
        if (a.getAttribute("href")) return;
        var name = (a.textContent || "").trim();
        if (!name) {
          var owner =
            a.parentElement && a.parentElement.querySelector(".menu-text");
          name = owner
            ? "Show or hide " + owner.textContent.trim()
            : "Show or hide section";
          asButton(a, name);
        } else {
          asButton(a);
        }
      });

    // Theme toggle: a link in Quarto; make it a button that Space also operates.
    document
      .querySelectorAll(".quarto-color-scheme-toggle")
      .forEach(function (t) {
        asButton(t, "Switch between light and dark theme");
      });

    // Phone menu: Escape closes it and returns focus to its button.
    document.addEventListener("keydown", function (ev) {
      if (ev.key !== "Escape") return;
      var side = document.getElementById("quarto-sidebar");
      if (!side || !side.classList.contains("show")) return;
      var btn = document.querySelector(
        '.quarto-btn-toggle, [data-bs-target*="quarto-sidebar"]',
      );
      if (btn) {
        btn.click();
        btn.focus();
      }
    });

    // Landmarks: name the two navigation regions.
    var sidebar = document.getElementById("quarto-sidebar");
    if (sidebar) sidebar.setAttribute("aria-label", "Workbook contents");
    var toc = document.getElementById("TOC");
    if (toc) toc.setAttribute("aria-label", "On this page");

    // Search box: Quarto builds it after load and keeps pointing its name at a
    // label that holds only the Submit button. Name it, and keep it named.
    function nameSearch(input) {
      if (input.getAttribute("aria-labelledby"))
        input.removeAttribute("aria-labelledby");
      if (input.getAttribute("aria-label") !== "Search this workbook")
        input.setAttribute("aria-label", "Search this workbook");
      if (input.getAttribute("placeholder") !== "Search this workbook")
        input.setAttribute("placeholder", "Search this workbook");
    }
    function watchSearch() {
      var input = document.querySelector("#quarto-search input, .aa-Input");
      if (!input) return false;
      nameSearch(input);
      new MutationObserver(function () {
        nameSearch(input);
      }).observe(input, {
        attributes: true,
        attributeFilter: ["aria-labelledby", "aria-label", "placeholder"],
      });
      return true;
    }
    if (!watchSearch()) {
      var box = document.getElementById("quarto-search") || document.body;
      var waiting = new MutationObserver(function () {
        if (watchSearch()) waiting.disconnect();
      });
      waiting.observe(box, { childList: true, subtree: true });
    }
    // However late the widget is built or rebuilt, name the box when it takes focus.
    // The phone search builds a fresh input each time it opens, and labels it
    // after it takes focus; watch each one.
    document.addEventListener("focusin", function (ev) {
      var t = ev.target;
      if (!(t && t.matches && t.matches(".aa-Input, #quarto-search input"))) return;
      nameSearch(t);
      if (!t._wbWatched) {
        t._wbWatched = true;
        new MutationObserver(function () {
          nameSearch(t);
        }).observe(t, { attributes: true, attributeFilter: ["aria-labelledby", "aria-label", "placeholder"] });
      }
    });

    // Entry lists: filter by any word in a row, or by one tag; sort by any keyed column.
    document
      .querySelectorAll(".wb-list[data-wb-filter]")
      .forEach(function (list) {
        var input = list.querySelector(".wb-list-tools input");
        var count = list.querySelector(".wb-list-count");
        var note = list.querySelector(".wb-list-tag");
        var body = list.querySelector("tbody");
        var rows = Array.prototype.slice.call(body.querySelectorAll("tr"));
        rows.forEach(function (r) {
          r._text = fold(r.getAttribute("data-search"));
          var tags = [];
          try {
            tags = JSON.parse(r.getAttribute("data-tags") || "[]");
          } catch (e) {}
          r._tags = Array.isArray(tags) ? tags.map(fold) : [];
        });
        var tag = null,
          tagShown = null;
        function apply() {
          var words = fold(input.value).split(/\s+/).filter(Boolean);
          var shown = 0;
          rows.forEach(function (r) {
            var ok = words.every(function (w) {
              return r._text.indexOf(w) !== -1;
            });
            if (tag) ok = ok && r._tags.indexOf(tag) !== -1;
            r.hidden = !ok;
            if (ok) shown++;
          });
          var filtered = words.length || tag;
          count.textContent = filtered
            ? shown + " of " + rows.length + " entries"
            : rows.length + " entries";
          if (note) {
            note.hidden = !tag;
            var label = note.querySelector(".wb-list-tag-name");
            if (label) label.textContent = tagShown || "";
          }
        }
        input.addEventListener("input", apply);
        if (note) {
          var clear = note.querySelector("button");
          if (clear)
            clear.addEventListener("click", function () {
              tag = null;
              tagShown = null;
              if (location.hash)
                history.replaceState(
                  null,
                  "",
                  location.pathname + location.search,
                );
              apply();
              input.focus();
            });
        }
        // catalogue.html#tag=sleep shows the entries with that tag;
        // catalogue.html#q=words arrives with the filter box filled in.
        function fromHash() {
          var mt = location.hash.match(/^#tag=(.*)$/);
          var mq = location.hash.match(/^#q=(.*)$/);
          if (mt) {
            tagShown = decode(mt[1]);
            tag = fold(tagShown);
          }
          if (mq) input.value = decode(mq[1]);
          if (mt || mq) apply();
        }
        fromHash();
        window.addEventListener("hashchange", fromHash);

        list.querySelectorAll("th button[data-key]").forEach(function (btn) {
          btn.addEventListener("click", function () {
            var key = btn.getAttribute("data-key");
            var th = btn.parentElement;
            var asc = th.getAttribute("aria-sort") !== "ascending";
            list.querySelectorAll("th[aria-sort]").forEach(function (h) {
              h.setAttribute("aria-sort", "none");
            });
            th.setAttribute("aria-sort", asc ? "ascending" : "descending");
            rows.sort(function (a, b) {
              var x = a.getAttribute("data-" + key) || "",
                y = b.getAttribute("data-" + key) || "";
              return x.localeCompare(y, undefined, { numeric: true, sensitivity: "base" }) * (asc ? 1 : -1);
            });
            rows.forEach(function (r) {
              body.appendChild(r);
            });
          });
        });
      });
  });
})();
