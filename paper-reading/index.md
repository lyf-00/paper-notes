---
layout: default
title: Paper Reading
navbar_title: Paper Reading
permalink: /paper-reading/
---

{% assign notes = site.pages | where: "public", true | where: "type", "paper-reading" | sort: "created_at" | reverse %}

<div class="row">
    <div class="col-lg-11 mx-auto">
        <section class="paper-reading-panel bg-white shadow-sm rounded-xl p-4 p-md-5" data-paper-reading-index>
            <div class="paper-reading-header">
                <div>
                    <h1 class="mb-2">Paper Reading</h1>
                    <div class="paper-reading-meta">
                        <span data-result-count>{{ notes | size }}</span> notes · sorted by created time
                    </div>
                </div>
                <div class="paper-header-tools">
                    <div class="paper-search-wrap">
                        <i class="fas fa-search" aria-hidden="true"></i>
                        <input
                            type="search"
                            class="paper-search-input"
                            placeholder="Search title, tag, source..."
                            aria-label="Search paper reading notes"
                            data-filter-search>
                    </div>
                    <label class="paper-sort-wrap">
                        <span>Sort</span>
                        <select data-sort-order aria-label="Sort paper reading notes">
                            <option value="created-desc">Newest</option>
                            <option value="created-asc">Oldest</option>
                            <option value="title-asc">Title</option>
                        </select>
                    </label>
                </div>
            </div>

            <div class="paper-filter-block" aria-label="Paper reading filters">
                <div class="paper-filter-row">
                    <div class="paper-filter-label">Category</div>
                    <div class="paper-filter-options" data-category-filters></div>
                </div>
                <div class="paper-filter-row">
                    <div class="paper-filter-label">Tag</div>
                    <div class="paper-filter-options" data-tag-filters></div>
                </div>
            </div>

            <div class="paper-list-toolbar">
                <div class="paper-page-summary" data-page-summary aria-live="polite"></div>
                <label class="paper-sort-wrap paper-page-size-wrap">
                    <span>Per Page</span>
                    <select data-page-size aria-label="Notes per page">
                        <option value="12">12</option>
                        <option value="24">24</option>
                        <option value="48">48</option>
                        <option value="all">All</option>
                    </select>
                </label>
            </div>

            <div class="wiki-list paper-note-list" data-paper-note-list>
                {% for note in notes %}
                {% capture search_text %}
                    {{ note.title }}
                    {{ note.paper_title }}
                    {{ note.description }}
                    {{ note.category }}
                    {{ note.venue }}
                    {{ note.year }}
                    {% for tag in note.tags %}{{ tag }} {% endfor %}
                {% endcapture %}
                <article
                    class="wiki-list-item paper-note-item"
                    data-category="{{ note.category | default: 'Uncategorized' | escape }}"
                    data-tags="{{ note.tags | join: '|' | escape }}"
                    data-created="{{ note.created_at | default: note.date | date_to_xmlschema }}"
                    data-title="{{ note.title | escape }}"
                    data-search="{{ search_text | strip_html | downcase | normalize_whitespace | escape }}">
                    <div class="paper-note-topline">
                        {% if note.category %}
                        <span class="paper-note-category">{{ note.category }}</span>
                        {% endif %}
                        {% if note.created_at %}
                        <time class="paper-note-time" datetime="{{ note.created_at | date_to_xmlschema }}">
                            {{ note.created_at | date: "%Y-%m-%d %H:%M" }}
                        </time>
                        {% elsif note.date %}
                        <time class="paper-note-time" datetime="{{ note.date | date_to_xmlschema }}">
                            {{ note.date | date: "%Y-%m-%d" }}
                        </time>
                        {% endif %}
                    </div>
                    <h2 class="h5 mb-2">
                        <a href="{{ note.url | relative_url }}">{{ note.title }}</a>
                    </h2>
                    {% if note.description %}
                    <p class="text-muted mb-2">{{ note.description }}</p>
                    {% endif %}
                    {% if note.tags %}
                    <div class="paper-note-tags" aria-label="Tags">
                        {% for tag in note.tags %}
                        <span class="paper-note-tag">{{ tag }}</span>
                        {% endfor %}
                    </div>
                    {% endif %}
                </article>
                {% endfor %}
            </div>

            <div class="paper-empty-state" data-empty-state hidden>No matching notes.</div>
            <nav class="paper-pagination" data-pagination aria-label="Paper reading pagination"></nav>
        </section>
    </div>
</div>

<script>
document.addEventListener("DOMContentLoaded", function() {
    var root = document.querySelector("[data-paper-reading-index]");
    if (!root) return;

    var items = Array.prototype.slice.call(root.querySelectorAll(".paper-note-item"));
    var list = root.querySelector("[data-paper-note-list]");
    var searchInput = root.querySelector("[data-filter-search]");
    var sortSelect = root.querySelector("[data-sort-order]");
    var pageSizeSelect = root.querySelector("[data-page-size]");
    var categoryWrap = root.querySelector("[data-category-filters]");
    var tagWrap = root.querySelector("[data-tag-filters]");
    var count = root.querySelector("[data-result-count]");
    var pageSummary = root.querySelector("[data-page-summary]");
    var pagination = root.querySelector("[data-pagination]");
    var emptyState = root.querySelector("[data-empty-state]");
    var activeCategory = "all";
    var activeTag = "all";
    var currentPage = 1;
    var filteredItems = items.slice();

    function normalize(value) {
        return String(value || "").trim();
    }

    function increment(map, key) {
        key = normalize(key);
        if (!key) return;
        map.set(key, (map.get(key) || 0) + 1);
    }

    function buildMapFromItems() {
        var categories = new Map();
        var tags = new Map();
        items.forEach(function(item) {
            increment(categories, item.dataset.category || "Uncategorized");
            normalize(item.dataset.tags).split("|").forEach(function(tag) {
                increment(tags, tag);
            });
        });
        return { categories: categories, tags: tags };
    }

    function makeButton(label, value, total, activeValue, onClick) {
        var button = document.createElement("button");
        var labelSpan = document.createElement("span");
        var totalSpan = document.createElement("span");
        button.type = "button";
        button.className = "paper-filter-btn";
        button.dataset.value = value;
        button.setAttribute("aria-pressed", value === activeValue ? "true" : "false");
        labelSpan.textContent = label;
        totalSpan.className = "paper-filter-count";
        totalSpan.textContent = total;
        button.appendChild(labelSpan);
        button.appendChild(totalSpan);
        button.addEventListener("click", onClick);
        return button;
    }

    function renderButtons(container, map, activeValue, onSelect, options) {
        var opts = options || {};
        container.innerHTML = "";
        container.appendChild(makeButton("All", "all", items.length, activeValue, function() {
            onSelect("all");
        }));
        var entries = Array.from(map.entries());
        if (opts.collapseAfter) {
            entries.sort(function(a, b) {
                return b[1] - a[1] || a[0].localeCompare(b[0]);
            });
        } else {
            entries.sort(function(a, b) {
                return a[0].localeCompare(b[0]);
            });
        }
        var visibleLimit = opts.collapseAfter && entries.length > opts.collapseAfter + 3
            ? opts.collapseAfter
            : entries.length;
        entries.forEach(function(entry, index) {
            var button = makeButton(entry[0], entry[0], entry[1], activeValue, function() {
                onSelect(entry[0]);
            });
            if (index >= visibleLimit && entry[0] !== activeValue) {
                button.hidden = true;
                button.dataset.overflow = "true";
            }
            container.appendChild(button);
        });
        if (visibleLimit < entries.length) {
            var hiddenCount = entries.length - visibleLimit;
            var moreButton = document.createElement("button");
            moreButton.type = "button";
            moreButton.className = "paper-filter-btn paper-filter-more";
            moreButton.setAttribute("aria-expanded", "false");
            moreButton.textContent = "+" + hiddenCount + " more";
            moreButton.addEventListener("click", function() {
                var expand = moreButton.getAttribute("aria-expanded") !== "true";
                Array.prototype.slice.call(container.querySelectorAll("[data-overflow]")).forEach(function(hiddenBtn) {
                    hiddenBtn.hidden = !expand;
                });
                moreButton.setAttribute("aria-expanded", String(expand));
                moreButton.textContent = expand ? "Show fewer" : "+" + hiddenCount + " more";
            });
            container.appendChild(moreButton);
        }
    }

    function updatePressed(container, activeValue) {
        Array.prototype.slice.call(container.querySelectorAll("button")).forEach(function(button) {
            if (!button.dataset.value) return;
            button.setAttribute("aria-pressed", button.dataset.value === activeValue ? "true" : "false");
        });
    }

    function itemTags(item) {
        return normalize(item.dataset.tags).split("|").filter(Boolean);
    }

    function sortedItems(sourceItems) {
        var mode = sortSelect.value;
        return sourceItems.slice().sort(function(a, b) {
            if (mode === "title-asc") {
                return normalize(a.dataset.title).localeCompare(normalize(b.dataset.title));
            }

            var aTime = Date.parse(a.dataset.created || "") || 0;
            var bTime = Date.parse(b.dataset.created || "") || 0;
            if (mode === "created-asc") {
                return aTime - bTime;
            }
            return bTime - aTime;
        });
    }

    function pageSize() {
        if (!pageSizeSelect || pageSizeSelect.value === "all") {
            return filteredItems.length || 1;
        }
        return parseInt(pageSizeSelect.value, 10) || 12;
    }

    function totalPages() {
        return Math.max(1, Math.ceil(filteredItems.length / pageSize()));
    }

    function clampPage() {
        currentPage = Math.min(Math.max(currentPage, 1), totalPages());
    }

    function makePageButton(label, page, options) {
        var button = document.createElement("button");
        var opts = options || {};
        button.type = "button";
        button.className = "paper-page-btn";
        button.textContent = label;
        button.disabled = !!opts.disabled;
        if (opts.current) {
            button.setAttribute("aria-current", "page");
        }
        button.addEventListener("click", function() {
            if (button.disabled || currentPage === page) return;
            currentPage = page;
            renderPage();
            var currentButton = pagination.querySelector('[aria-current="page"]');
            if (currentButton) currentButton.focus();
        });
        return button;
    }

    function visiblePageNumbers() {
        var pages = totalPages();
        var values = [];
        var start = Math.max(1, currentPage - 2);
        var end = Math.min(pages, currentPage + 2);

        values.push(1);
        for (var page = start; page <= end; page += 1) {
            if (values.indexOf(page) === -1) values.push(page);
        }
        if (values.indexOf(pages) === -1) values.push(pages);
        return values.sort(function(a, b) { return a - b; });
    }

    function renderPagination() {
        if (!pagination) return;
        pagination.innerHTML = "";

        if (filteredItems.length === 0 || pageSizeSelect.value === "all" || totalPages() <= 1) {
            pagination.hidden = true;
            return;
        }

        pagination.hidden = false;
        pagination.appendChild(makePageButton("Prev", currentPage - 1, {
            disabled: currentPage === 1
        }));

        var pages = visiblePageNumbers();
        pages.forEach(function(page, index) {
            if (index > 0 && page - pages[index - 1] > 1) {
                var gap = document.createElement("span");
                gap.className = "paper-page-gap";
                gap.textContent = "...";
                pagination.appendChild(gap);
            }
            pagination.appendChild(makePageButton(String(page), page, {
                current: page === currentPage
            }));
        });

        pagination.appendChild(makePageButton("Next", currentPage + 1, {
            disabled: currentPage === totalPages()
        }));
    }

    function updatePageSummary(start, end) {
        if (!pageSummary) return;
        if (filteredItems.length === 0) {
            pageSummary.textContent = "Showing 0 notes";
            return;
        }
        pageSummary.textContent = "Showing " + start + "-" + end + " of " + filteredItems.length + " notes";
    }

    function renderPage() {
        if (!list) return;
        clampPage();

        var size = pageSize();
        var startIndex = (currentPage - 1) * size;
        var endIndex = Math.min(startIndex + size, filteredItems.length);
        var pageItems = filteredItems.slice(startIndex, endIndex);

        items.forEach(function(item) {
            item.hidden = true;
        });

        pageItems.forEach(function(item) {
            item.hidden = false;
            list.appendChild(item);
        });

        updatePageSummary(filteredItems.length ? startIndex + 1 : 0, endIndex);
        renderPagination();
    }

    function applyFilters(resetPage) {
        var query = normalize(searchInput.value).toLowerCase();

        filteredItems = sortedItems(items.filter(function(item) {
            var matchesSearch = !query || normalize(item.dataset.search).indexOf(query) !== -1;
            var matchesCategory = activeCategory === "all" || item.dataset.category === activeCategory;
            var matchesTag = activeTag === "all" || itemTags(item).indexOf(activeTag) !== -1;
            return matchesSearch && matchesCategory && matchesTag;
        }));

        if (resetPage) {
            currentPage = 1;
        }

        count.textContent = filteredItems.length;
        emptyState.hidden = filteredItems.length !== 0;
        updatePressed(categoryWrap, activeCategory);
        updatePressed(tagWrap, activeTag);
        renderPage();
    }

    var maps = buildMapFromItems();
    renderButtons(categoryWrap, maps.categories, activeCategory, function(value) {
        activeCategory = value;
        applyFilters(true);
    });
    renderButtons(tagWrap, maps.tags, activeTag, function(value) {
        activeTag = value;
        applyFilters(true);
    }, { collapseAfter: 15 });

    searchInput.addEventListener("input", function() {
        applyFilters(true);
    });
    if (sortSelect) {
        sortSelect.addEventListener("change", function() {
            applyFilters(true);
        });
    }
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener("change", function() {
            applyFilters(true);
        });
    }
    applyFilters(true);
});
</script>
