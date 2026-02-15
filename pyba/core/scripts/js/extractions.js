(config) => {
    const anchors = Array.from(document.querySelectorAll(config.link_selector));
    const results = [];

    for (const a of anchors) {
        let titleEl = null;

        titleEl = a.querySelector(config.title_selector);

        let title =
            titleEl?.textContent?.trim() ||
            a.getAttribute(config.usual_title_name) ||        // The second fallback from titleEl
            a.getAttribute(config.label_name) ||     // The third fallback
            "";

        if (title && a.href && a.getAttribute('href').startsWith(config.usual_relative_link_format)) {
            results.push({
                title,
                href: new URL(a.getAttribute('href'), window.location.origin).href
            });
        }
    }

    // Removing duplicates
    const seen = new Set();
    return results.filter(v => {
        if (seen.has(v.href)) return false;
        seen.add(v.href);
        return true;
    });
    }