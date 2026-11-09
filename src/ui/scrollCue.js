// @ts-check
// v1.0 (iPhone): a scrolling list (the shop, the bag) shows that there is more below it: the menu
// gets the class `more-below` (a fade at the list's bottom edge and a small ▼, styles.css) until
// the list is scrolled to its end. On a small landscape phone the list often scrolls.

/** Whether `el` has content below what it shows (1 px of slack for fractional layouts). @param {{ scrollTop: number, clientHeight: number, scrollHeight: number }} el */
export function hasMoreBelow(el) {
  return el.scrollTop + el.clientHeight < el.scrollHeight - 1;
}

/**
 * Keeps `menu.classList` `more-below` in step with `list`'s scroll position. Call the returned
 * function after the list's content changes or the menu opens.
 * @param {HTMLElement} menu @param {() => HTMLElement | null} getList the current scrolling list
 * @returns {() => void}
 */
export function scrollCue(menu, getList) {
  const update = () => {
    const list = getList();
    menu.classList.toggle('more-below', !!list && !menu.hidden && hasMoreBelow(list));
  };
  // Scroll events do not bubble, but they reach a capturing listener on an ancestor.
  menu.addEventListener('scroll', update, { capture: true, passive: true });
  window.addEventListener('resize', update);
  return () => {
    update();
    requestAnimationFrame(update); // after layout (the menu was just shown or re-rendered)
  };
}
