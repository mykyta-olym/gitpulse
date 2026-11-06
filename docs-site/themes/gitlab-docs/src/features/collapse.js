/**
 * Bootstrap-style collapse toggle
 *
 * Adapted from https://medium.com/dailyjs/mimicking-bootstraps-collapse-with-vanilla-javascript-b3bb389040e7
 *
 * This version includes handling for aria-hidden and aria-expanded attributes,
 * which should be included on any collapsible element.
 *
 * Usage is the same as Bootstrap:
 * https://getbootstrap.com/docs/4.0/components/collapse/#via-data-attributes
 */
export const expandCollapse = () => {
  const triggers = document.querySelectorAll('[data-toggle="collapse"]');

  const collapse = (selector, cmd) => {
    const targets = document.querySelectorAll(selector);

    targets.forEach((target) => {
      target.classList[cmd]("show");
      target.setAttribute("aria-hidden", cmd === "remove");
    });
  };

  triggers.forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const target = document.querySelector(
        trigger.getAttribute("data-target"),
      );
      const expanded = target.classList.contains("show");
      trigger.setAttribute("aria-expanded", !expanded);
      collapse(
        trigger.getAttribute("data-target"),
        expanded ? "remove" : "add",
      );

      // Add a class to the body tag when collapsible content is expanded
      const label = trigger
        .getAttribute("data-target")
        .replace(/[#.>+=~$]/g, ""); // Drop special characters so that we get a valid class name

      document
        .querySelector("body")
        .classList.toggle(`collapsible-${label}-open`);
    });
  });
};
