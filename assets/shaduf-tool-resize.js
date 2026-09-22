(() => {
  if (window.__shadufToolResize) return
  const initialize = () => {
    if (window.__shadufToolResize === true) return
    const roots = document.querySelectorAll('[data-shaduf-resize-root]')
    if (roots.length !== 1) {
      delete window.__shadufToolResize
      return
    }
    const root = roots[0]
    window.__shadufToolResize = true

    let scheduled = false
    let lastHeight = 0
    const measure = (force = false) => {
      scheduled = false
      const rect = root.getBoundingClientRect()
      const style = getComputedStyle(root)
      const margins = (Number.parseFloat(style.marginTop) || 0) + (Number.parseFloat(style.marginBottom) || 0)
      const borders = (Number.parseFloat(style.borderTopWidth) || 0) + (Number.parseFloat(style.borderBottomWidth) || 0)
      const height = Math.max(1, Math.ceil(Math.max(rect.height, root.scrollHeight + borders) + margins))
      if (!force && height === lastHeight) return
      lastHeight = height
      parent.postMessage({ type: 'shaduf:resize', height }, '*')
    }
    const schedule = () => {
      if (scheduled) return
      scheduled = true
      queueMicrotask(measure)
    }

    addEventListener('message', (event) => {
      if (event.source === parent && event.data?.type === 'shaduf:measure') measure(true)
    })
    addEventListener('resize', schedule)
    addEventListener('load', schedule)
    document.addEventListener('toggle', schedule, true)
    new ResizeObserver(schedule).observe(root)
    new MutationObserver(schedule).observe(root, { attributes: true, childList: true, characterData: true, subtree: true })
    document.fonts?.ready.then(schedule, schedule)
    for (const image of document.images) if (!image.complete) {
      image.addEventListener('load', schedule, { once: true })
      image.addEventListener('error', schedule, { once: true })
    }
    parent.postMessage({ type: 'shaduf:ready' }, '*')
    schedule()
  }

  if (document.readyState === 'loading') {
    window.__shadufToolResize = 'pending'
    document.addEventListener('DOMContentLoaded', initialize, { once: true })
  } else initialize()
})()
