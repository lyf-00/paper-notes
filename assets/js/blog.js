(function () {
    var content = document.querySelector(".blog-content");
    if (!content) return;

    var navbarHeight = 88;
    var article = document.querySelector(".wiki-note-card");

    function initReadingSurface() {
        if (!article || !article.hasAttribute("data-reading-surface")) return;

        var nodes = Array.prototype.slice.call(content.childNodes);
        var fragment = document.createDocumentFragment();
        var section = null;
        var sectionIndex = -1;

        nodes.forEach(function (node) {
            var startsSection = node.nodeType === 1 && node.tagName === "H1";

            if (!section && node.nodeType === 3 && !node.textContent.trim()) return;

            if (startsSection || !section) {
                sectionIndex += 1;
                section = document.createElement("section");
                section.className = sectionIndex === 0
                    ? "reading-surface-section reading-surface-hero"
                    : "reading-surface-section reading-surface-doc";
                fragment.appendChild(section);
            }

            section.appendChild(node);
        });

        content.appendChild(fragment);

        var kicker = article.getAttribute("data-kicker");
        if (kicker) {
            Array.prototype.slice.call(content.querySelectorAll(".reading-surface-doc > h1")).forEach(function (h1) {
                var label = document.createElement("p");
                label.className = "doc-kicker";
                label.textContent = kicker;
                h1.parentNode.insertBefore(label, h1);
            });
        }
    }

    initReadingSurface();

    var headings = Array.prototype.slice.call(content.querySelectorAll("h1, h2, h3"));
    var tocHeadings = article && article.hasAttribute("data-reading-surface")
        ? Array.prototype.slice.call(content.querySelectorAll("h1, h2"))
        : headings;

    function slugify(text, fallback) {
        var slug = String(text || "")
            .trim()
            .toLowerCase()
            .replace(/<[^>]+>/g, "")
            .replace(/&[a-z0-9#]+;/g, "")
            .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, "-")
            .replace(/^-+|-+$/g, "");
        return slug || fallback;
    }

    function ensureHeadingIds() {
        var seen = {};
        headings.forEach(function (heading, index) {
            var base = heading.id || slugify(heading.textContent, "section-" + (index + 1));
            var unique = base;
            var count = 2;

            while (seen[unique] || document.getElementById(unique)) {
                if (heading.id === unique) break;
                unique = base + "-" + count;
                count += 1;
            }

            heading.id = unique;
            seen[unique] = true;
            heading.style.scrollMarginTop = navbarHeight + "px";
        });
    }

    function initAnchors() {
        if (!window.anchors) return;

        window.anchors.options = {
            visible: "hover",
            placement: "left",
            icon: "#",
            class: "heading-anchor"
        };
        window.anchors.add(".blog-content h2, .blog-content h3, .blog-content h4");
    }

    function manualToc(tocList) {
        tocHeadings.forEach(function (heading) {
            var link = document.createElement("a");
            link.href = "#" + heading.id;
            link.textContent = heading.textContent;
            link.className = "toc-link toc-" + heading.tagName.toLowerCase();
            link.addEventListener("click", function (event) {
                event.preventDefault();
                window.scrollTo({
                    top: heading.offsetTop - navbarHeight,
                    behavior: "smooth"
                });
                history.pushState(null, "", "#" + heading.id);
            });
            tocList.appendChild(link);
        });

        function updateActive() {
            var scrollPos = window.scrollY + navbarHeight + 16;
            var current = null;
            tocHeadings.forEach(function (heading) {
                if (heading.offsetTop <= scrollPos) {
                    current = heading.id;
                }
            });
            Array.prototype.slice.call(tocList.querySelectorAll("a")).forEach(function (link) {
                link.classList.toggle("toc-active", link.getAttribute("href") === "#" + current);
            });
        }

        window.addEventListener("scroll", updateActive, { passive: true });
        updateActive();
    }

    function initToc() {
        var tocNav = document.getElementById("blog-toc");
        var tocList = document.querySelector(".blog-toc-list");
        if (!tocNav || !tocList) return;

        if (tocHeadings.length === 0) {
            tocNav.hidden = true;
            return;
        }

        if (window.tocbot) {
            var isReadingSurface = article && article.hasAttribute("data-reading-surface");
            window.tocbot.init({
                tocSelector: ".blog-toc-list",
                contentSelector: ".blog-content",
                headingSelector: isReadingSurface ? "h1, h2" : "h1, h2, h3",
                hasInnerContainers: true,
                orderedList: false,
                collapseDepth: 6,
                headingsOffset: navbarHeight + 12,
                scrollSmooth: true,
                scrollSmoothOffset: -navbarHeight,
                listClass: "toc-list",
                listItemClass: "toc-list-item",
                linkClass: "toc-link",
                activeLinkClass: "toc-active"
            });
            return;
        }

        manualToc(tocList);
    }

    function initMobileToc() {
        var details = document.querySelector(".mobile-toc");
        var container = document.getElementById("blog-toc-list-mobile");
        var source = document.getElementById("blog-toc-list");
        if (!details || !container) return;
        if (tocHeadings.length === 0 || !source || !source.innerHTML.trim()) {
            details.hidden = true;
            return;
        }
        container.innerHTML = source.innerHTML;
        container.addEventListener("click", function (event) {
            if (event.target.closest("a")) details.removeAttribute("open");
        });
    }

    function initTocToggle() {
        var wrapper = document.querySelector(".blog-layout-wrapper");
        var toggle = document.getElementById("blog-toc-toggle");
        if (!wrapper || !toggle) return;

        var storageKey = "paper-notes:toc-collapsed";

        function setCollapsed(collapsed) {
            wrapper.classList.toggle("toc-collapsed", collapsed);
            toggle.setAttribute("aria-expanded", String(!collapsed));
            toggle.setAttribute("aria-label", collapsed ? "展开目录" : "收起目录");
            toggle.title = collapsed ? "展开目录" : "收起目录";
        }

        var initialState = false;
        try {
            initialState = window.localStorage.getItem(storageKey) === "true";
        } catch (error) {
            initialState = false;
        }
        setCollapsed(initialState);

        toggle.addEventListener("click", function () {
            var collapsed = !wrapper.classList.contains("toc-collapsed");
            setCollapsed(collapsed);
            try {
                window.localStorage.setItem(storageKey, String(collapsed));
            } catch (error) {
                // The toggle still works when storage is unavailable.
            }
        });
    }

    function initImageZoom() {
        if (!window.mediumZoom) return;

        window.mediumZoom(".blog-content img:not(.no-zoom)", {
            background: "rgba(243, 246, 245, 0.96)",
            margin: 32,
            scrollOffset: 0
        });
    }

    function detectImageSourceKind(img) {
        var manualSource = (img.dataset && img.dataset.source) || "";
        var className = img.className || "";
        var src = (img.getAttribute("src") || img.currentSrc || "").toLowerCase();

        if (manualSource === "generated" || /\bfigure-generated\b/.test(className)) {
            return "generated";
        }
        if (manualSource === "original" || /\bfigure-original\b/.test(className)) {
            return "original";
        }

        var markedAncestor = img.closest(".figure-generated, .figure-original");
        if (markedAncestor) {
            return markedAncestor.classList.contains("figure-generated") ? "generated" : "original";
        }

        return /\.svg(?:$|[?#])/.test(src) ? "generated" : "original";
    }

    function labelImagesBySource() {
        Array.prototype.slice.call(content.querySelectorAll("img")).forEach(function (img) {
            if (img.closest(".image-source-frame") || img.classList.contains("no-source-label")) return;

            var sourceKind = detectImageSourceKind(img);
            var frame = document.createElement("span");
            var badge = document.createElement("span");

            frame.className = "image-source-frame image-source-" + sourceKind;
            frame.setAttribute(
                "data-source-kind",
                sourceKind === "generated" ? "generated" : "original"
            );

            badge.className = "image-source-badge";
            badge.textContent = sourceKind === "generated" ? "自制图解" : "原文图 / 截图";
            frame.appendChild(badge);

            img.parentNode.insertBefore(frame, img);
            frame.appendChild(img);
        });
    }

    function initReadingProgress() {
        var bar = document.querySelector(".reading-progress span");
        var article = document.querySelector(".wiki-note-card");
        if (!bar || !article) return;

        function updateProgress() {
            var start = article.offsetTop - navbarHeight;
            var end = start + article.offsetHeight - window.innerHeight + navbarHeight;
            var ratio = end > start ? (window.scrollY - start) / (end - start) : 1;
            var clamped = Math.max(0, Math.min(1, ratio));
            bar.style.transform = "scaleX(" + clamped + ")";
        }

        window.addEventListener("scroll", updateProgress, { passive: true });
        window.addEventListener("resize", updateProgress);
        updateProgress();
    }

    function wrapTables() {
        Array.prototype.slice.call(content.querySelectorAll("table")).forEach(function (table) {
            if (table.parentElement && table.parentElement.classList.contains("table-scroll")) return;
            var wrapper = document.createElement("div");
            wrapper.className = "table-scroll";
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        });
    }

    function markExternalLinks() {
        Array.prototype.slice.call(content.querySelectorAll("a[href^='http']")).forEach(function (link) {
            if (link.hostname === window.location.hostname) return;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
        });
    }

    ensureHeadingIds();
    initToc();
    initMobileToc();
    initTocToggle();
    initAnchors();
    labelImagesBySource();
    initImageZoom();
    initReadingProgress();
    wrapTables();
    markExternalLinks();
})();
