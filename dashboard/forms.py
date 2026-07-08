# dashboard/forms.py
from django import forms
from app.models import CustomUser, Stock, Transaction, AdminWallet, Trader, UserCopyTraderHistory, Card
from decimal import Decimal
from django.utils.safestring import mark_safe


class FmpComboboxWidget(forms.Widget):
    """
    FMP-powered asset combobox — trigger button + dropdown panel with search.
    Submits just the symbol string as the field value.
    """

    def render(self, name, value, attrs=None, renderer=None):
        import json
        from django.utils.html import escape
        from app.models import Asset, Stock

        attrs = attrs or {}
        field_id = attrs.get('id', f'id_{name}')
        current = escape(value or '')

        # Build local dataset: Asset model + Stock model + MARKET_CHOICES
        local = []
        seen = set()
        for a in Asset.objects.all().order_by('symbol').values('symbol', 'category'):
            sym = a['symbol']
            if sym and sym not in seen:
                local.append({'symbol': sym, 'name': a.get('category', ''), 'cat': a.get('category', '')})
                seen.add(sym)
        for s in Stock.objects.filter(is_active=True).order_by('symbol').values('symbol', 'name', 'category'):
            sym = s['symbol']
            if sym and sym not in seen:
                local.append({'symbol': sym, 'name': s['name'] or '', 'cat': s.get('category', '')})
                seen.add(sym)
        for sym, label in UserCopyTraderHistory.MARKET_CHOICES:
            if sym not in seen:
                local.append({'symbol': sym, 'name': label, 'cat': ''})
                seen.add(sym)

        local_json = json.dumps(local)

        # Resolve display label for a pre-existing value
        init_label = ''
        if current:
            for item in local:
                if item['symbol'] == current:
                    init_label = item['name']
                    break

        has_val = 'true' if current else 'false'
        trigger_label = escape(f"{current}  —  {init_label}" if (current and init_label) else (current or ''))

        html = f"""
<style>
/* ── trigger button ── */
#fmp-trigger-{field_id} {{
  width:100%; display:flex; align-items:center; gap:10px;
  padding:0 12px; min-height:42px; box-sizing:border-box;
  background:#1e293b; border:1px solid #475569; border-radius:8px;
  cursor:pointer; text-align:left; transition:border-color .15s;
  font-family:inherit;
}}
#fmp-trigger-{field_id}:hover {{ border-color:#818cf8; }}
#fmp-trigger-{field_id}.fmp-open-{field_id} {{ border-color:#818cf8; border-bottom-left-radius:0; border-bottom-right-radius:0; border-bottom-color:#334155; box-shadow:0 0 0 2px rgba(129,140,248,.2); }}

/* ── dropdown panel ── */
#fmp-panel-{field_id} {{
  display:none; position:absolute; z-index:9999; left:0; right:0;
  background:#1e293b; border:1px solid #818cf8;
  border-top:none; border-bottom-left-radius:8px; border-bottom-right-radius:8px;
  box-shadow:0 12px 40px rgba(0,0,0,.6);
}}

/* ── search box ── */
#fmp-search-wrap-{field_id} {{
  display:flex; align-items:center; gap:8px;
  margin:10px 10px 6px; padding:0 10px;
  background:#0f172a; border:1px solid #475569; border-radius:6px;
  min-height:36px; transition:border-color .15s;
}}
#fmp-search-wrap-{field_id}:focus-within {{ border-color:#818cf8; box-shadow:0 0 0 2px rgba(129,140,248,.2); }}

#fmp-search-{field_id} {{
  border:none !important; outline:none; flex:1; font-size:13px;
  background:transparent !important; color:#f1f5f9 !important;
  padding:0; font-family:inherit; box-shadow:none !important;
}}
#fmp-search-{field_id}::placeholder {{ color:#64748b !important; }}

/* ── options list ── */
#fmp-list-{field_id} {{ max-height:248px; overflow-y:auto; padding:4px 0; }}
#fmp-list-{field_id}::-webkit-scrollbar {{ width:4px; }}
#fmp-list-{field_id}::-webkit-scrollbar-track {{ background:transparent; }}
#fmp-list-{field_id}::-webkit-scrollbar-thumb {{ background:#334155; border-radius:2px; }}

.fmp-opt-{field_id} {{
  display:flex; align-items:center; gap:10px;
  padding:8px 14px; cursor:pointer; border-bottom:1px solid #0f172a;
  transition:background .1s;
}}
.fmp-opt-{field_id}:last-child {{ border-bottom:none; }}
.fmp-opt-{field_id}:hover {{ background:#334155; }}
.fmp-opt-{field_id}.fmp-selected-{field_id} {{ background:rgba(99,102,241,.12); }}

@keyframes fmp-spin-{field_id} {{
  from {{ transform:rotate(0deg); }} to {{ transform:rotate(360deg); }}
}}
</style>

<div style="position:relative;width:100%;">

  <!-- ── Trigger ── -->
  <button type="button" id="fmp-trigger-{field_id}">
    <!-- Logo slot -->
    <div id="fmp-t-logo-wrap-{field_id}"
         style="display:{('flex' if current else 'none')};align-items:center;width:24px;height:24px;flex-shrink:0;">
      <img id="fmp-t-logo-{field_id}"
           src="https://financialmodelingprep.com/image-stock/{current}.png"
           style="width:24px;height:24px;object-fit:contain;border-radius:3px;"
           onerror="this.style.display='none';document.getElementById('fmp-t-av-{field_id}').style.display='flex'">
      <div id="fmp-t-av-{field_id}"
           style="display:none;width:24px;height:24px;background:#4f46e5;border-radius:4px;
                  color:#fff;font-size:8px;font-weight:800;align-items:center;justify-content:center;">
        {current[:3] if current else ''}
      </div>
    </div>
    <!-- Label -->
    <span id="fmp-t-label-{field_id}"
          style="flex:1;font-size:13.5px;color:{'#f1f5f9' if current else '#64748b'};
                 white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
      {trigger_label if trigger_label else 'Select market / asset…'}
    </span>
    <!-- Chevron -->
    <svg id="fmp-chevron-{field_id}"
         style="width:16px;height:16px;flex-shrink:0;color:#64748b;transition:transform .2s;"
         viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <path d="M6 9l6 6 6-6"/>
    </svg>
  </button>

  <!-- ── Hidden value ── -->
  <input type="hidden" name="{name}" id="{field_id}" value="{current}">

  <!-- ── Dropdown panel ── -->
  <div id="fmp-panel-{field_id}">
    <!-- Search -->
    <div id="fmp-search-wrap-{field_id}">
      <svg style="width:14px;height:14px;color:#64748b;flex-shrink:0;"
           viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
      </svg>
      <input type="text" id="fmp-search-{field_id}" placeholder="Search…" autocomplete="off">
      <!-- Spinner -->
      <svg id="fmp-spin-{field_id}"
           style="display:none;width:14px;height:14px;flex-shrink:0;color:#818cf8;
                  animation:fmp-spin-{field_id} .7s linear infinite;"
           viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
      </svg>
    </div>
    <!-- List -->
    <div id="fmp-list-{field_id}"></div>
  </div>
</div>

<script>
(function(){{
  var LOCAL    = {local_json};
  var trigger  = document.getElementById('fmp-trigger-{field_id}');
  var panel    = document.getElementById('fmp-panel-{field_id}');
  var search   = document.getElementById('fmp-search-{field_id}');
  var list     = document.getElementById('fmp-list-{field_id}');
  var spin     = document.getElementById('fmp-spin-{field_id}');
  var hidden   = document.getElementById('{field_id}');
  var chevron  = document.getElementById('fmp-chevron-{field_id}');
  var tLogoWrap= document.getElementById('fmp-t-logo-wrap-{field_id}');
  var tLogo    = document.getElementById('fmp-t-logo-{field_id}');
  var tAv      = document.getElementById('fmp-t-av-{field_id}');
  var tLabel   = document.getElementById('fmp-t-label-{field_id}');
  if (!trigger || !panel || !search || !list || !hidden) return;

  var open = false, fmpTm, currentSym = '{current}', currentName = {json.dumps(init_label)};

  /* ── open / close ── */
  function openPanel() {{
    open = true;
    panel.style.display = 'block';
    trigger.classList.add('fmp-open-{field_id}');
    chevron.style.transform = 'rotate(180deg)';
    search.value = '';
    renderList(LOCAL.slice(0, 40));
    setTimeout(function() {{ search.focus(); }}, 40);
  }}

  function closePanel() {{
    open = false;
    panel.style.display = 'none';
    trigger.classList.remove('fmp-open-{field_id}');
    chevron.style.transform = '';
    spin.style.display = 'none';
    clearTimeout(fmpTm);
  }}

  trigger.addEventListener('click', function(e) {{
    e.stopPropagation();
    open ? closePanel() : openPanel();
  }});

  document.addEventListener('click', function(e) {{
    if (open && !panel.contains(e.target) && e.target !== trigger) closePanel();
  }});

  /* ── search ── */
  search.addEventListener('input', function() {{
    var q = search.value.trim();
    if (!q) {{ renderList(LOCAL.slice(0, 40)); spin.style.display = 'none'; return; }}
    renderList(filterLocal(q));
    clearTimeout(fmpTm);
    spin.style.display = 'block';
    fmpTm = setTimeout(function() {{ fetchFmp(q); }}, 380);
  }});

  search.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') closePanel();
  }});

  /* ── filter / fetch ── */
  function filterLocal(q) {{
    var ql = q.toLowerCase();
    return LOCAL.filter(function(it) {{
      return (it.symbol + ' ' + it.name).toLowerCase().indexOf(ql) !== -1;
    }}).slice(0, 30);
  }}

  function fetchFmp(q) {{
    fetch('/dashboard/api/fmp-search/?q=' + encodeURIComponent(q))
      .then(function(r) {{ return r.ok ? r.json() : []; }})
      .then(function(fmpItems) {{
        spin.style.display = 'none';
        if (!Array.isArray(fmpItems)) return;
        var localSyms = new Set(filterLocal(q).map(function(x) {{ return x.symbol; }}));
        var extra = fmpItems
          .filter(function(it) {{ return it.symbol && !localSyms.has(it.symbol); }})
          .map(function(it) {{ return {{symbol: it.symbol, name: it.name || '', cat: '', fmp: true}}; }});
        renderList(filterLocal(q).concat(extra));
      }})
      .catch(function() {{ spin.style.display = 'none'; }});
  }}

  /* ── select ── */
  function selectItem(sym, name) {{
    currentSym = sym; currentName = name;
    hidden.value = sym;
    tLabel.textContent = name ? sym + '  —  ' + name : sym;
    tLabel.style.color = '#f1f5f9';
    tLogoWrap.style.display = 'flex';
    tLogo.style.display = 'block';
    tLogo.src = 'https://financialmodelingprep.com/image-stock/' + sym + '.png';
    tAv.textContent = sym.slice(0, 3);
    tAv.style.display = 'none';
    closePanel();
  }}

  /* ── render list ── */
  function renderList(items) {{
    list.innerHTML = '';
    if (!items.length) {{
      var empty = document.createElement('div');
      empty.style.cssText = 'padding:14px 16px;color:#64748b;font-size:13px;text-align:center;';
      empty.textContent = 'No matching assets found';
      list.appendChild(empty);
      return;
    }}
    items.forEach(function(it) {{
      if (!it.symbol) return;
      var row = document.createElement('div');
      row.className = 'fmp-opt-{field_id}' + (it.symbol === currentSym ? ' fmp-selected-{field_id}' : '');

      /* Logo */
      var img = document.createElement('img');
      img.src = 'https://financialmodelingprep.com/image-stock/' + it.symbol + '.png';
      img.style.cssText = 'width:28px;height:28px;object-fit:contain;flex-shrink:0;border-radius:4px;';
      var av = document.createElement('div');
      av.style.cssText = 'display:none;width:28px;height:28px;background:#4f46e5;border-radius:4px;' +
                         'color:#fff;font-size:8px;font-weight:800;align-items:center;justify-content:center;flex-shrink:0;';
      av.textContent = it.symbol.slice(0, 3);
      img.onerror = function() {{ img.style.display = 'none'; av.style.display = 'flex'; }};

      /* Text */
      var info = document.createElement('div');
      info.style.cssText = 'flex:1;min-width:0;';
      var symEl = document.createElement('span');
      symEl.style.cssText = 'font-weight:700;font-size:13px;color:#f1f5f9;';
      symEl.textContent = it.symbol;
      info.appendChild(symEl);
      if (it.name) {{
        var nm = document.createElement('span');
        nm.style.cssText = 'color:#94a3b8;font-size:12px;margin-left:6px;';
        nm.textContent = '— ' + it.name;
        info.appendChild(nm);
      }}

      /* Right side: badges + checkmark */
      var right = document.createElement('div');
      right.style.cssText = 'display:flex;align-items:center;gap:5px;flex-shrink:0;';

      if (it.cat) {{
        var catB = document.createElement('span');
        catB.style.cssText = 'font-size:10px;padding:1px 5px;border-radius:3px;font-weight:600;' +
                             'background:rgba(79,70,229,.25);color:#a5b4fc;text-transform:uppercase;';
        catB.textContent = it.cat;
        right.appendChild(catB);
      }}
      if (it.fmp) {{
        var fmpB = document.createElement('span');
        fmpB.style.cssText = 'font-size:10px;padding:1px 5px;border-radius:3px;font-weight:600;' +
                             'background:rgba(5,78,22,.35);color:#4ade80;';
        fmpB.textContent = 'FMP';
        right.appendChild(fmpB);
      }}
      if (it.symbol === currentSym) {{
        var chk = document.createElement('span');
        chk.style.cssText = 'color:#818cf8;font-size:15px;font-weight:700;margin-left:2px;';
        chk.textContent = '✓';
        right.appendChild(chk);
      }}

      row.appendChild(img);
      row.appendChild(av);
      row.appendChild(info);
      row.appendChild(right);

      row.addEventListener('mousedown', function(e) {{
        e.preventDefault();
        selectItem(it.symbol, it.name || '');
      }});
      list.appendChild(row);
    }});
  }}
}})();
</script>"""
        return mark_safe(html)

    def value_from_datadict(self, data, files, name):
        return data.get(name, '')


class FmpStockSymbolWidget(forms.TextInput):
    """Symbol input for the Stock admin — shows FMP logo preview and auto-fills Name."""

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        field_id = attrs.get('id', f'id_{name}')
        html = super().render(name, value, attrs, renderer)
        init_val = (value or '').strip().upper()
        display = 'flex' if init_val else 'none'
        preview_html = f"""
<div id="fmp-prev-{field_id}" style="margin-top:6px;display:{display};align-items:center;gap:10px;">
  <img id="fmp-img-{field_id}"
       src="https://financialmodelingprep.com/image-stock/{init_val}.png"
       style="width:48px;height:48px;object-fit:contain;border:1px solid #e5e7eb;border-radius:8px;background:#f9fafb;"
       onerror="document.getElementById('fmp-prev-{field_id}').style.display='none'">
  <small style="color:#6b7280;">FMP logo (used automatically if no image is uploaded)</small>
</div>
<script>
(function(){{
  var sym  = document.getElementById('{field_id}');
  var prev = document.getElementById('fmp-prev-{field_id}');
  var img  = document.getElementById('fmp-img-{field_id}');
  if (!sym) return;
  var tm;
  sym.addEventListener('input', function(){{
    var v = sym.value.trim().toUpperCase();
    if (!v) {{ if (prev) prev.style.display = 'none'; return; }}
    if (img) {{
      img.src = 'https://financialmodelingprep.com/image-stock/' + v + '.png';
      if (prev) prev.style.display = 'flex';
    }}
    clearTimeout(tm);
    tm = setTimeout(function(){{
      fetch('/dashboard/api/fmp-search/?q=' + encodeURIComponent(v))
        .then(function(r){{ return r.json(); }})
        .then(function(items){{
          if (!Array.isArray(items) || !items.length) return;
          var exact = items.find(function(it){{ return it.symbol && it.symbol.toUpperCase() === v; }});
          var match = exact || items[0];
          if (match && match.name) {{
            var nameInp = document.getElementById('id_name');
            if (nameInp && !nameInp.value) nameInp.value = match.name;
          }}
        }})
        .catch(function(){{}});
    }}, 400);
  }});
}})();
</script>"""
        return mark_safe(html + preview_html)

class AddTradeForm(forms.Form):
    """Form for adding trades with extensive dropdowns"""
    
    # User selection
    user_email = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True).order_by('email'),
        label="Select User",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        }),
        to_field_name='email'
    )
    
    # Entry amount
    entry = forms.DecimalField(
        label="Entry Amount",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '5255'
        })
    )
    
    # Asset type
    ASSET_TYPE_CHOICES = [
        ('', 'Select Type'),
        ('stock', 'Stock'),
        ('crypto', 'Crypto'),
        ('forex', 'Forex'),
    ]
    
    asset_type = forms.ChoiceField(
        choices=ASSET_TYPE_CHOICES,
        label="Type",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Asset (populated dynamically based on type)
    asset = forms.CharField(
        label="Asset",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Select type first'
        })
    )
    
    # Direction
    DIRECTION_CHOICES = [
        ('', 'Select Direction'),
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('futures', 'Futures'),
    ]
    
    direction = forms.ChoiceField(
        choices=DIRECTION_CHOICES,
        label="Direction",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Profit/Loss
    profit = forms.DecimalField(
        label="Profit/Loss",
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '0.00'
        })
    )
    
    # Duration
    DURATION_CHOICES = [
        ('', 'Select Duration'),
        ('2 minutes', '2 minutes'),
        ('5 minutes', '5 minutes'),
        ('30 minutes', '30 minutes'),
        ('1 hour', '1 hour'),
        ('8 hours', '8 hours'),
        ('10 hours', '10 hours'),
        ('20 hours', '20 hours'),
        ('1 day', '1 day'),
        ('2 days', '2 days'),
        ('3 days', '3 days'),
        ('4 days', '4 days'),
        ('5 days', '5 days'),
        ('6 days', '6 days'),
        ('1 week', '1 week'),
        ('2 weeks', '2 weeks'),
    ]
    
    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        label="Duration",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Rate (optional)
    rate = forms.DecimalField(
        label="Rate (Optional)",
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '251'
        })
    )


class AddEarningsForm(forms.Form):
    """Quick form for adding earnings to users"""

    DESTINATION_CHOICES = [
        ('balance', 'Balance'),
        ('profit', 'Profit'),
    ]

    user_email = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True).order_by('email'),
        label="Select User",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
        }),
        to_field_name='email'
    )

    destination = forms.ChoiceField(
        choices=DESTINATION_CHOICES,
        label="Add to",
        initial='balance',
        widget=forms.RadioSelect(attrs={
            'class': 'destination-radio',
        })
    )

    amount = forms.DecimalField(
        label="Earnings Amount",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': '100.00'
        })
    )

    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'Bonus, Referral, Trade Profit, etc.'
        })
    )


class ApproveDepositForm(forms.Form):
    """Form for approving deposits"""
    
    STATUS_CHOICES = [
        ('completed', 'Approve'),
        ('failed', 'Reject'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Action",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    admin_notes = forms.CharField(
        label="Admin Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Internal notes about this transaction...'
        })
    )


class ApproveWithdrawalForm(forms.Form):
    """Form for approving withdrawals"""
    
    STATUS_CHOICES = [
        ('completed', 'Approve'),
        ('failed', 'Reject'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Action",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    admin_notes = forms.CharField(
        label="Admin Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Internal notes about this withdrawal...'
        })
    )


class ApproveKYCForm(forms.Form):
    """Form for approving KYC submissions"""
    
    ACTION_CHOICES = [
        ('approve', 'Approve KYC'),
        ('reject', 'Reject KYC'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        label="Action",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    admin_notes = forms.CharField(
        label="Admin Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Reason for rejection or any notes...'
        })
    )


# dashboard/forms.py - Updated AddCopyTradeForm
class AddCopyTradeForm(forms.Form):
    """Form for adding copy trade history - LEVERAGE REMOVED"""
    
    # User selection
    # user = forms.ModelChoiceField(
    #     queryset=CustomUser.objects.filter(is_active=True).order_by('email'),
    #     label="Select User",
    #     widget=forms.Select(attrs={
    #         'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
    #         'id': 'id_user'
    #     }),
    #     empty_label="Select User"
    # )
    
    # Trader selection
    trader = forms.ModelChoiceField(
        queryset=Trader.objects.filter(is_active=True).order_by('name'),
        label="Select Trader",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
        }),
        empty_label="Select Trader"
    )
    
    # Market selection — FMP combobox
    market = forms.CharField(
        label="Market / Asset",
        max_length=50,
        widget=FmpComboboxWidget(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        }),
    )

    # Direction
    direction = forms.ChoiceField(
        choices=[('', 'Select Direction')] + list(UserCopyTraderHistory.DIRECTION_CHOICES),
        label="Trade Direction",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # LEVERAGE FIELD REMOVED
    
    # Duration
    DURATION_CHOICES = [
        ('', 'Select Duration'),
        ('2 minutes', '2 Minutes'),
        ('5 minutes', '5 Minutes'),
        ('10 minutes', '10 Minutes'),
        ('15 minutes', '15 Minutes'),
        ('30 minutes', '30 Minutes'),
        ('1 hour', '1 Hour'),
        ('2 hours', '2 Hours'),
        ('4 hours', '4 Hours'),
        ('12 hours', '12 Hours'),
        ('1 day', '1 Day'),
        ('2 days', '2 Days'),
        ('1 week', '1 Week'),
        ('2 weeks', '2 Weeks'),
        ('1 month', '1 Month'),
    ]
    
    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        label="Trade Duration",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Amount
    amount = forms.DecimalField(
        label="Investment Amount",
        max_digits=20,
        decimal_places=8,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '1000.00',
            'step': '0.00000001'
        })
    )
    
    # Entry Price
    entry_price = forms.DecimalField(
        label="Entry Price",
        max_digits=20,
        decimal_places=8,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '50000.00',
            'step': '0.00000001'
        })
    )
    
    # Exit Price (Optional)
    exit_price = forms.DecimalField(
        label="Exit Price (Optional)",
        max_digits=20,
        decimal_places=8,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '51000.00',
            'step': '0.00000001'
        })
    )
    
    # Profit/Loss
    profit_loss_percent = forms.DecimalField(
        label="Profit / Loss %",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
            'placeholder': '15.50 (positive for profit, negative for loss)',
            'step': '0.01'
        }),
        help_text="Enter as percentage (e.g., 15.50 for +15.5% gain)"
    )
    
    # Status
    status = forms.ChoiceField(
        choices=[('', 'Select Status')] + list(UserCopyTraderHistory.STATUS_CHOICES),
        label="Trade Status",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    # Closed At (Optional)
    closed_at = forms.DateTimeField(
        label="Close Date & Time (Optional)",
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'type': 'datetime-local',
            'placeholder': 'Leave blank if trade is still open'
        })
    )
    
    # Notes
    notes = forms.CharField(
        label="Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Additional notes about this trade...'
        })
    )

class AddTraderForm(forms.Form):
    """Form for adding professional traders - direct input, no dropdown/range combos"""

    _i = 'w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition'
    _s = _i
    _f = 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'
    _c = 'w-4 h-4 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500'

    # --- Basic Info ---
    name = forms.CharField(
        label="Trader Name",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': _i, 'placeholder': 'Kristijan'
        })
    )
    
    username = forms.CharField(
        label="Username", max_length=100,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '@kristijan'}),
        help_text="Must be unique"
    )
    avatar = forms.ImageField(
        label="Avatar Image", required=False,
        widget=forms.FileInput(attrs={'class': _f, 'accept': 'image/*'})
    )
    country_flag = forms.ImageField(
        label="Country Flag Image", required=False,
        widget=forms.FileInput(attrs={'class': _f, 'accept': 'image/*'})
    )

    COUNTRY_CHOICES = [
        ('', 'Select Country'),
        ('United States', 'United States'), ('United Kingdom', 'United Kingdom'),
        ('Germany', 'Germany'), ('France', 'France'), ('Canada', 'Canada'),
        ('Australia', 'Australia'), ('Singapore', 'Singapore'), ('Hong Kong', 'Hong Kong'),
        ('Japan', 'Japan'), ('South Korea', 'South Korea'), ('India', 'India'),
        ('Brazil', 'Brazil'), ('Mexico', 'Mexico'), ('Netherlands', 'Netherlands'),
        ('Switzerland', 'Switzerland'), ('Sweden', 'Sweden'), ('Norway', 'Norway'),
        ('Denmark', 'Denmark'), ('Spain', 'Spain'), ('Italy', 'Italy'), ('Other', 'Other'),
    ]
    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES, label="Country",
        widget=forms.Select(attrs={'class': _s})
    )
    badge = forms.ChoiceField(
        choices=[('', 'Select Badge'), ('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold')],
        label="Badge Level",
        widget=forms.Select(attrs={'class': _s})
    )

    # --- Capital & Gain ---
    capital = forms.CharField(
        label="Starting Capital ($)", max_length=50,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '50000'})
    )
    gain = forms.DecimalField(
        label="Total Gain (%)", max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '126799.00', 'step': '0.01'})
    )

    # --- Risk & Time ---
    RISK_CHOICES = [(i, str(i)) for i in range(1, 11)]
    risk = forms.ChoiceField(
        choices=[('', 'Select Risk Level')] + RISK_CHOICES,
        label="Risk Level (1-10)",
        widget=forms.Select(attrs={'class': _s})
    )
    AVG_TRADE_TIME_CHOICES = [
        ('', 'Select Avg Trade Time'),
        ('1 day', '1 Day'), ('3 days', '3 Days'), ('1 week', '1 Week'), ('2 weeks', '2 Weeks'),
        ('3 weeks', '3 Weeks'), ('1 month', '1 Month'), ('2 months', '2 Months'),
        ('3 months', '3 Months'), ('6 months', '6 Months'),
    ]
    avg_trade_time = forms.ChoiceField(
        choices=AVG_TRADE_TIME_CHOICES, label="Avg Trade Time",
        widget=forms.Select(attrs={'class': _s})
    )

    # --- Copiers & Trades ---
    copiers = forms.IntegerField(
        label="Current Copiers",
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '40', 'min': '0'})
    )
    trades = forms.IntegerField(
        label="Total Trades",
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '251', 'min': '0'})
    )

    # --- Performance Stats ---
    avg_profit_percent = forms.DecimalField(
        label="Avg Profit %", max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '86.00', 'step': '0.01'})
    )
    avg_loss_percent = forms.DecimalField(
        label="Avg Loss %", max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '8.00', 'step': '0.01'})
    )
    total_wins = forms.IntegerField(
        label="Total Wins",
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '1166', 'min': '0'})
    )
    total_losses = forms.IntegerField(
        label="Total Losses",
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '160', 'min': '0'})
    )

    # --- Additional Stats ---
    subscribers = forms.IntegerField(
        label="Subscribers", required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '49', 'min': '0'})
    )
    current_positions = forms.IntegerField(
        label="Current Open Positions", required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '3', 'min': '0'})
    )
    expert_rating = forms.DecimalField(
        label="Expert Rating (out of 5.00)", max_digits=3, decimal_places=2, required=False, initial=5.00,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '4.80', 'step': '0.01', 'min': '0', 'max': '5'})
    )
    min_account_threshold = forms.DecimalField(
        label="Min Account Balance ($)", max_digits=12, decimal_places=2, required=False, initial=0.00,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '50000.00', 'step': '0.01'})
    )

    # --- Performance Metrics ---
    return_ytd = forms.DecimalField(
        label="Return YTD %", max_digits=10, decimal_places=2, required=False, initial=0.00,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '2187.00', 'step': '0.01'})
    )
    return_2y = forms.DecimalField(
        label="Return 2 Years %", max_digits=10, decimal_places=2, required=False, initial=0.00,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '5000.00', 'step': '0.01'})
    )
    avg_score_7d = forms.DecimalField(
        label="Avg Score (7 days)", max_digits=10, decimal_places=2, required=False, initial=0.00,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '9.30', 'step': '0.01'})
    )
    profitable_weeks = forms.DecimalField(
        label="Profitable Weeks %", max_digits=5, decimal_places=2, required=False, initial=0.00,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '92.00', 'step': '0.01'})
    )
    total_trades_12m = forms.IntegerField(
        label="Total Trades (12 months)", required=False, initial=0,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '150', 'min': '0'})
    )

    # --- Profit Share ---
    profit_share = forms.IntegerField(
        label="Profit Share %", required=False, initial=50,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '50', 'min': '0', 'max': '100'})
    )

    # --- Status ---
    is_active = forms.BooleanField(
        label="Active (Available for Copying)", required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': _c})
    )


class EditTraderForm(AddTraderForm):
    """Inherits all fields from AddTraderForm."""
    pass


class EditDepositForm(forms.Form):
    """Form for editing deposit details"""
    
    # Amount
    amount = forms.DecimalField(
        label="Deposit Amount",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '1000.00',
            'step': '0.01'
        })
    )
    
    # Currency
    CURRENCY_CHOICES = [
        ('BTC', 'Bitcoin (BTC)'),
        ('ETH', 'Ethereum (ETH)'),
        ('SOL', 'Solana (SOL)'),
        ('USDT ERC20', 'USDT (ERC20)'),
        ('USDT TRC20', 'USDT (TRC20)'),
        ('BNB', 'Binance Coin (BNB)'),
        ('TRX', 'Tron (TRX)'),
        ('USDC', 'USDC (BASE)'),
    ]
    
    currency = forms.ChoiceField(
        choices=CURRENCY_CHOICES,
        label="Currency",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    # Unit (crypto amount)
    unit = forms.DecimalField(
        label="Crypto Unit Amount",
        max_digits=12,
        decimal_places=8,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '0.01234567',
            'step': '0.00000001'
        }),
        help_text="Amount of cryptocurrency deposited"
    )
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Status",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
        })
    )
    
    # Description
    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'Deposit description...'
        })
    )
    
    # Reference
    reference = forms.CharField(
        label="Reference Number",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'DEP-XXXXXXXXXX'
        })
    )
    
    # Receipt (optional - for updating)
    receipt = forms.ImageField(
        label="Update Receipt (Optional)",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'accept': 'image/*'
        }),
        help_text="Leave blank to keep existing receipt"
    )


class AddUserDirectTradeForm(forms.Form):
    """Form to add a trade directly to a specific user (not tied to a trader)."""

    _input = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
    _select = _input
    _textarea = _input

    market = forms.CharField(
        label="Market / Asset",
        max_length=50,
        widget=FmpComboboxWidget(attrs={'class': _select}),
    )

    DIRECTION_CHOICES = [('', 'Select Direction'), ('buy', 'Buy'), ('sell', 'Sell')]
    direction = forms.ChoiceField(
        choices=DIRECTION_CHOICES,
        label="Trade Direction",
        widget=forms.Select(attrs={'class': _select}),
    )

    DURATION_CHOICES = [
        ('', 'Select Duration'),
        ('2 minutes', '2 Minutes'), ('5 minutes', '5 Minutes'), ('10 minutes', '10 Minutes'),
        ('15 minutes', '15 Minutes'), ('30 minutes', '30 Minutes'),
        ('1 hour', '1 Hour'), ('2 hours', '2 Hours'), ('4 hours', '4 Hours'), ('12 hours', '12 Hours'),
        ('1 day', '1 Day'), ('2 days', '2 Days'),
        ('1 week', '1 Week'), ('2 weeks', '2 Weeks'), ('1 month', '1 Month'),
    ]
    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        label="Trade Duration",
        widget=forms.Select(attrs={'class': _select}),
    )

    entry_price = forms.DecimalField(
        label="Entry Price",
        max_digits=20,
        decimal_places=8,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '50000.00', 'step': '0.00000001'}),
    )

    exit_price = forms.DecimalField(
        label="Exit Price (Optional)",
        max_digits=20,
        decimal_places=8,
        required=False,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '51000.00', 'step': '0.00000001'}),
    )

    profit_loss_percent = forms.DecimalField(
        label="Profit / Loss %",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _input, 'placeholder': '15.50', 'step': '0.01'}),
        help_text="Positive for profit, negative for loss",
    )

    STATUS_CHOICES = [('', 'Select Status'), ('open', 'Open'), ('closed', 'Closed')]
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Trade Status",
        widget=forms.Select(attrs={'class': _select}),
    )

    closed_at = forms.DateTimeField(
        label="Close Date & Time (Optional)",
        required=False,
        widget=forms.DateTimeInput(attrs={'class': _input, 'type': 'datetime-local'}),
    )

    notes = forms.CharField(
        label="Notes (Optional)",
        required=False,
        widget=forms.Textarea(attrs={'class': _textarea, 'rows': 3, 'placeholder': 'Additional notes...'}),
    )

# ---------------------------------------------------------------------------
# Admin Wallet Form
# ---------------------------------------------------------------------------

class AdminWalletForm(forms.Form):
    _i = 'w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition'
    _s = _i
    _f = 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'
    _c = 'w-4 h-4 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500'

    currency = forms.ChoiceField(
        choices=[('', 'Select Currency')] + list(AdminWallet.CURRENCY_CHOICES),
        label="Currency",
        widget=forms.Select(attrs={'class': _s}),
    )
    amount = forms.DecimalField(
        label="Rate (USD per unit)",
        max_digits=20, decimal_places=6,
        widget=forms.NumberInput(attrs={'class': _i, 'placeholder': '97250.00', 'step': '0.000001'}),
    )
    wallet_address = forms.CharField(
        label="Wallet Address", max_length=255,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh'}),
    )
    qr_code = forms.ImageField(
        label="QR Code (Optional)", required=False,
        widget=forms.FileInput(attrs={'class': _f, 'accept': 'image/*'}),
    )
    is_active = forms.BooleanField(
        label="Active (Visible to Users)", required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': _c}),
    )


# ---------------------------------------------------------------------------
# Card Edit Form (admin)
# ---------------------------------------------------------------------------

class CardEditForm(forms.Form):
    _i = 'w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition'
    _s = _i
    _c = 'w-4 h-4 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500'

    cardholder_name = forms.CharField(
        label="Cardholder Name", max_length=255,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': 'John Doe'}),
    )
    card_number = forms.CharField(
        label="Card Number", max_length=19,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '4242424242424242'}),
    )
    expiry_month = forms.CharField(
        label="Expiry Month", max_length=2,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '12'}),
    )
    expiry_year = forms.CharField(
        label="Expiry Year", max_length=4,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '2028'}),
    )
    cvv = forms.CharField(
        label="CVV", max_length=4,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '123'}),
    )
    card_type = forms.ChoiceField(
        choices=Card.CARD_TYPE_CHOICES, label="Card Type",
        widget=forms.Select(attrs={'class': _s}),
    )
    billing_address = forms.CharField(
        label="Billing Address", max_length=500, required=False,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '123 Main St'}),
    )
    billing_zip = forms.CharField(
        label="Billing Zip", max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': _i, 'placeholder': '10001'}),
    )
    is_default = forms.BooleanField(
        label="Default Card", required=False,
        widget=forms.CheckboxInput(attrs={'class': _c}),
    )


_f = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'


class EditCopyTradeForm(forms.Form):
    """Form for editing an existing copy trade record"""

    market = forms.CharField(
        label="Market / Asset",
        max_length=50,
        widget=FmpComboboxWidget(attrs={'class': _f}),
    )
    direction = forms.ChoiceField(
        choices=[('', 'Select Direction')] + list(UserCopyTraderHistory.DIRECTION_CHOICES),
        label="Trade Direction",
        widget=forms.Select(attrs={'class': _f}),
    )
    duration = forms.ChoiceField(
        choices=[
            ('', 'Select Duration'),
            ('2 minutes', '2 Minutes'), ('5 minutes', '5 Minutes'),
            ('10 minutes', '10 Minutes'), ('15 minutes', '15 Minutes'),
            ('30 minutes', '30 Minutes'), ('1 hour', '1 Hour'),
            ('2 hours', '2 Hours'), ('4 hours', '4 Hours'),
            ('12 hours', '12 Hours'), ('1 day', '1 Day'),
            ('2 days', '2 Days'), ('1 week', '1 Week'),
            ('2 weeks', '2 Weeks'), ('1 month', '1 Month'),
        ],
        label="Trade Duration",
        widget=forms.Select(attrs={'class': _f}),
    )
    amount = forms.DecimalField(
        label="Investment Amount", max_digits=20, decimal_places=8,
        widget=forms.NumberInput(attrs={'class': _f, 'placeholder': '1000.00', 'step': '0.00000001'}),
    )
    entry_price = forms.DecimalField(
        label="Entry Price", max_digits=20, decimal_places=8,
        widget=forms.NumberInput(attrs={'class': _f, 'placeholder': '50000.00', 'step': '0.00000001'}),
    )
    exit_price = forms.DecimalField(
        label="Exit Price (Optional)", max_digits=20, decimal_places=8, required=False,
        widget=forms.NumberInput(attrs={'class': _f, 'placeholder': '51000.00', 'step': '0.00000001'}),
    )
    profit_loss_percent = forms.DecimalField(
        label="Profit / Loss %", max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _f, 'placeholder': '15.50', 'step': '0.01'}),
        help_text="Positive = profit, negative = loss",
    )
    status = forms.ChoiceField(
        choices=[('', 'Select Status')] + list(UserCopyTraderHistory.STATUS_CHOICES),
        label="Trade Status",
        widget=forms.Select(attrs={'class': _f}),
    )
    closed_at = forms.DateTimeField(
        label="Close Date & Time (Optional)", required=False,
        widget=forms.DateTimeInput(attrs={'class': _f, 'type': 'datetime-local'}),
    )
    notes = forms.CharField(
        label="Notes (Optional)", required=False,
        widget=forms.Textarea(attrs={'class': _f, 'rows': 3}),
    )


# ===== User Edit Form =====

class UserEditForm(forms.Form):
    _input = 'w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
    _select = _input
    _checkbox = 'w-4 h-4 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500'

    # Account
    first_name  = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'class': _input}))
    last_name   = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'class': _input}))
    email       = forms.EmailField(widget=forms.EmailInput(attrs={'class': _input}))
    phone       = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'class': _input}))
    currency    = forms.CharField(required=False, max_length=10, widget=forms.TextInput(attrs={'class': _input, 'placeholder': 'USD'}))
    dob         = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': _input, 'type': 'date'}))

    # Location
    country     = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'class': _input}))
    region      = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'class': _input}))
    city        = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'class': _input}))
    address     = forms.CharField(required=False, max_length=500, widget=forms.TextInput(attrs={'class': _input}))
    postal_code = forms.CharField(required=False, max_length=500, widget=forms.TextInput(attrs={'class': _input}))

    # Financials
    balance = forms.DecimalField(max_digits=20, decimal_places=2, widget=forms.NumberInput(attrs={'class': _input, 'step': '0.01'}))
    profit  = forms.DecimalField(max_digits=20, decimal_places=2, widget=forms.NumberInput(attrs={'class': _input, 'step': '0.01'}))
    target  = forms.DecimalField(max_digits=20, decimal_places=2, widget=forms.NumberInput(attrs={'class': _input, 'step': '0.01'}), help_text="Portfolio target for the progress bar")

    # KYC
    ID_TYPE_CHOICES = [('', '-'), ('passport', 'Passport'), ('driver_license', "Driver's License"), ('national_id', 'National ID'), ('voter_card', "Voter's Card")]
    id_type = forms.ChoiceField(choices=ID_TYPE_CHOICES, required=False, widget=forms.Select(attrs={'class': _select}))

    # Loyalty
    LOYALTY_CHOICES = [('iron', 'Iron'), ('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold'), ('platinum', 'Platinum'), ('diamond', 'Diamond'), ('elite', 'Elite')]
    current_loyalty_status = forms.ChoiceField(choices=LOYALTY_CHOICES, widget=forms.Select(attrs={'class': _select}))
    next_loyalty_status    = forms.ChoiceField(choices=LOYALTY_CHOICES, widget=forms.Select(attrs={'class': _select}))
    next_amount_to_upgrade = forms.DecimalField(max_digits=20, decimal_places=2, widget=forms.NumberInput(attrs={'class': _input, 'step': '0.01'}))

    # Permissions
    is_active          = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': _checkbox}))
    is_verified        = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': _checkbox}))
    email_verified     = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': _checkbox}))
    can_transfer       = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': _checkbox}))
    two_factor_enabled = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': _checkbox}))
    is_staff           = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': _checkbox}))

    # Dev password
    new_password = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': _input, 'placeholder': 'Leave blank to keep current', 'autocomplete': 'new-password'}))


# ===== Stock Form =====

class StockForm(forms.Form):
    _input = 'w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
    _checkbox = 'w-4 h-4 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500'

    symbol = forms.CharField(
        label="Ticker Symbol (e.g. AAPL)", max_length=20,
        widget=FmpStockSymbolWidget(attrs={'class': _input, 'placeholder': 'AAPL'}),
        help_text="Logo and full name will be fetched from FMP automatically.",
    )
    name = forms.CharField(
        label="Full Name", max_length=200,
        widget=forms.TextInput(attrs={'class': _input, 'placeholder': 'Apple Inc.'}),
        help_text="Auto-filled from FMP when you type the symbol (you can override).",
    )
    image = forms.ImageField(
        label="Custom Logo (optional)",
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': _input, 'accept': 'image/*'}),
        help_text="Leave blank to use FMP's logo automatically.",
    )
    CATEGORY_CHOICES = [
        ('stock',   'Stock'),
        ('crypto',  'Crypto'),
        ('etf',     'ETF'),
        ('indices', 'Indices'),
        ('forex',   'Forex'),
    ]
    category = forms.ChoiceField(
        label="Category",
        choices=CATEGORY_CHOICES,
        initial='stock',
        widget=forms.Select(attrs={'class': _input}),
    )
    is_active = forms.BooleanField(
        label="Active (Visible to users)", required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': _checkbox}),
    )
    is_featured = forms.BooleanField(
        label="Featured (Show prominently)", required=False,
        widget=forms.CheckboxInput(attrs={'class': _checkbox}),
    )


class EditWithdrawalForm(forms.Form):
    """Form for editing withdrawal details"""

    _wi = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
    _ws = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white'

    amount = forms.DecimalField(
        label="Withdrawal Amount",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': _wi, 'placeholder': '1000.00', 'step': '0.01'}),
    )

    CURRENCY_CHOICES = [
        ('BTC', 'Bitcoin (BTC)'),
        ('ETH', 'Ethereum (ETH)'),
        ('SOL', 'Solana (SOL)'),
        ('USDT ERC20', 'USDT (ERC20)'),
        ('USDT TRC20', 'USDT (TRC20)'),
        ('BNB', 'Binance Coin (BNB)'),
        ('TRX', 'Tron (TRX)'),
        ('USDC', 'USDC (BASE)'),
    ]

    currency = forms.ChoiceField(
        choices=CURRENCY_CHOICES,
        label="Currency",
        widget=forms.Select(attrs={'class': _ws}),
    )

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="Status",
        widget=forms.Select(attrs={'class': _ws}),
    )

    description = forms.CharField(
        label="Description / Notes",
        required=False,
        widget=forms.Textarea(attrs={
            'class': _wi,
            'rows': 3,
            'placeholder': 'Admin notes or withdrawal description…',
        }),
    )

    reference = forms.CharField(
        label="Reference Number",
        max_length=100,
        widget=forms.TextInput(attrs={'class': _wi, 'placeholder': 'TXN-XXXXXX-XX'}),
    )
