(config) => {
    const validTags = new Set(config.valid_tags);
    const invalidTypes = new Set(config.invalid_input_types);

    const candidates = document.querySelectorAll('input, textarea, select, [contenteditable="true"]');
    const seen = new Set();
    const results = [];

    for (const el of candidates) {
        const tag = el.tagName.toLowerCase();
        if (!validTags.has(tag)) continue;

        const type = (el.type || 'text').toLowerCase();
        if (invalidTypes.has(type)) continue;

        if (el.readOnly || el.disabled) continue;

        const rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) continue;

        const id = el.id || null;
        const name = el.name || null;
        const placeholder = el.placeholder || null;
        const ariaLabel = el.getAttribute('aria-label') || null;

        let selector;
        if (id) {
            selector = '#' + id;
        } else if (name) {
            selector = tag + "[name='" + name + "']";
        } else if (placeholder) {
            selector = tag + "[placeholder='" + placeholder + "']";
        } else if (ariaLabel) {
            selector = tag + "[aria-label='" + ariaLabel + "']";
        } else {
            continue;
        }

        if (seen.has(selector)) continue;
        seen.add(selector);

        results.push({
            tag: tag,
            type: type,
            id: id,
            name: name,
            placeholder: placeholder,
            aria_label: ariaLabel,
            selector: selector
        });
    }

    return results;
}
