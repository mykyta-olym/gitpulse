/* ============================================
   GlFormSelect - Alpine component for <select> replacement
   Used by the select_field() Jinja2 macro (forms.html).
   Renders a GitLab Pajamas-style dropdown that:
     * submits via a hidden <input> (works with FormData & form.el.value)
     * syncs bi-directionally when external JS sets .value
     * fires native "change" events for data-change-action handlers
   ============================================ */
window.glFormSelect = function glFormSelect(cfg) {
  const _opts = Object.fromEntries(cfg.options || []);
  return {
    open: false,
    selected: String(cfg.value ?? ''),
    opts: _opts,
    placeholder: cfg.placeholder || '',
    get label() { return this.opts[this.selected] || ''; },

    /* Alpine init hook */
    init: function () {
      // Default to first option when no value & no placeholder
      if (!this.selected && !this.placeholder && cfg.options?.length) {
        this.selected = String(cfg.options[0][0]);
      }

      // Intercept .value property on hidden <input> so external JS
      // setting el.value = 'x' also updates Alpine state.
      const inp  = this.$refs.input;
      const validator = this.$refs.validator || null;
      const self = this;
      const desc = Object.getOwnPropertyDescriptor(
        HTMLInputElement.prototype, 'value'
      );
      const raw  = function (v) { desc.set.call(inp, v); };

      Object.defineProperty(inp, 'value', {
        get: function ()  { return desc.get.call(inp); },
        set: function (v) {
          raw(v);
          v = inp.value;
          // A value set from outside that is not among the rendered options
          // (e.g. an archived course's academic year, outside the generated
          // year range) used to select "nothing" and render a blank control.
          // Adopt it as its own option so the real value is always visible.
          if (v && !(v in self.opts)) {
            inp.addOptions([[v, v]]);
          }
          if (self.selected !== v) self.selected = v;
        },
        configurable: true
      });

      // Alpine -> hidden <input> sync + fire native change
      this.$watch('selected', function (v) {
        raw(v);
        self.syncOptions();
        if (validator) {
          validator.value = v;
          if (v) {
            validator.setCustomValidity('');
            self.$el.classList.remove('is-invalid');
          }
        }
        inp.dispatchEvent(new Event('change', { bubbles: true }));
      });

      if (validator) {
        validator.value = this.selected || '';
        validator.addEventListener('invalid', function (event) {
          event.preventDefault();
          self.$el.classList.add('is-invalid');
          self.open = true;
          const toggle = self.$el.querySelector('.gl-form-dropdown-toggle');
          if (toggle) toggle.focus();
        });
      }

      /* Open/close motion. The panel rises the last few pixels in and leaves
         the same way; the close is deferred until the fade finishes, which is
         the whole reason x-show could not stay - it removed the element on the
         same tick the flag changed. */
      const menu = this.$refs.menu;
      if (menu) {
        menu.style.display = 'none';
        menu.inert = true;
        this.$watch('open', function (v) {
          // Return focus before hiding a picked option, including during the
          // exit animation. An outside click keeps its own new focus target.
          if (!v && menu.contains(document.activeElement)) {
            self.$el.querySelector('.gl-form-dropdown-toggle').focus({ preventScroll: true });
          }
          menu.inert = !v;
          if (v) {
            menu.style.display = '';
            /* Same one moment, same one helper as the JS dropdowns - see
               GP.positionDropdownMenu. The body-wide MutationObserver that used
               to answer this for both is gone. */
            if (typeof GP.positionDropdownMenu === 'function') GP.positionDropdownMenu(menu);
            GP.motion.popIn(menu);
          } else {
            GP.motion.popOut(menu, function () {
              menu.style.display = 'none';
              GP.motion.settle(menu, 'opacity,transform');
            });
          }
        });
      }

      // Boost ancestor card z-index when dropdown is open
      const card = this.$el.closest('.card');
      if (card) {
        this.$watch('open', function (v) { card.classList.toggle('has-dropdown-open', v); });
      }

      // Boost ancestor form-group z-index when dropdown is open
      const fg = this.$el.closest('.form-group');
      if (fg) {
        this.$watch('open', function (v) {
          if (v) { fg.style.position = 'relative'; fg.style.zIndex = '100'; }
          else   { fg.style.position = ''; fg.style.zIndex = ''; }
        });
      }

      // Expose addOptions() on the hidden <input> so external JS can
      // dynamically populate this dropdown (e.g. filter options from API).
      const _self = this;
      inp.addOptions = function (newOpts) {
        const menu = _self.$refs.menu;
        if (!menu) return;
        newOpts.forEach(function (opt) {
          const v = String(opt[0]), l = opt[1];
          if (_self.opts[v] !== undefined) return;
          _self.opts[v] = l;
          const sizingLabel = document.createElement('span');
          sizingLabel.textContent = l;
          _self.$refs.sizer.appendChild(sizingLabel);
          const li = document.createElement('li');
          li.setAttribute('role', 'option');
          const b = document.createElement('button');
          b.type = 'button';
          b.className = 'gl-dropdown-item';
          b.dataset.value = v;
          b.addEventListener('click', function () { _self.select(v); });
          b.innerHTML =
            GP.icons.get('check', 16, 'icon icon-sm gl-dropdown-item-check') +
            '<span class="gl-dropdown-item-content"><span class="gl-dropdown-item-title">' +
            escapeHtml(l) + '</span></span>';
          li.appendChild(b);
          menu.appendChild(li);
        });
        if (menu.querySelector('.gl-dropdown-item')) {
          menu.querySelector('.gl-dropdown-empty')?.remove();
        }
        _self.syncOptions();
      };
      inp.optionCount = function () { return Object.keys(_self.opts).length; };
      this.syncOptions();

      const modal = this.$el.closest('.modal-backdrop');
      if (modal) {
        this._onModalClosed = function (event) {
          if (event.detail?.id === modal.id) self.open = false;
        };
        document.addEventListener('modal-closed', this._onModalClosed);
      }
    },

    destroy: function () {
      if (this._onModalClosed) {
        document.removeEventListener('modal-closed', this._onModalClosed);
      }
    },

    // Server-rendered and subsequently loaded options share one selected state.
    syncOptions: function () {
      this.$refs.menu.querySelectorAll('.gl-dropdown-item').forEach((button) => {
        const selected = button.dataset.value === this.selected;
        button.classList.toggle('active', selected);
        button.parentElement.setAttribute('aria-selected', String(selected));
      });
    },

    onKeydown: function (event) {
      const toggle = this.$el.querySelector('.gl-form-dropdown-toggle');
      if (toggle.disabled) return;
      if (event.key === 'Escape') {
        if (!this.open) return;
        event.preventDefault();
        event.stopPropagation(); // dismiss the list before its containing dialog
        this.open = false;
        toggle.focus({ preventScroll: true });
        return;
      }
      if (event.key === 'Tab') {
        if (this.open) {
          toggle.focus({ preventScroll: true });
          this.open = false;
        }
        return;
      }
      const arrows = event.key === 'ArrowDown' || event.key === 'ArrowUp';
      if (!arrows && !(this.open && (event.key === 'Home' || event.key === 'End'))) return;
      event.preventDefault();
      const wasOpen = this.open;
      this.open = true;
      this.$nextTick(() => {
        const buttons = Array.from(this.$refs.menu.querySelectorAll('.gl-dropdown-item:not(:disabled)'));
        if (!buttons.length) return;
        let index = buttons.indexOf(document.activeElement);
        if (!wasOpen) index = buttons.findIndex(b => b.dataset.value === this.selected);
        else if (event.key === 'Home') index = 0;
        else if (event.key === 'End') index = buttons.length - 1;
        else index = (index + (event.key === 'ArrowDown' ? 1 : -1) + buttons.length) % buttons.length;
        if (index < 0) index = event.key === 'ArrowUp' ? buttons.length - 1 : 0;
        buttons[index].focus({ preventScroll: true });
        buttons[index].scrollIntoView({ block: 'nearest' });
      });
    },

    /* Called by option buttons */
    select: function (v) { this.selected = String(v); this.open = false; }
  };
};
