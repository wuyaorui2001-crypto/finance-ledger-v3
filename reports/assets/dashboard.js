(function () {
  "use strict";

  let dashboardData = null;
  let currentYear = null;

  function formatMoney(n) {
    return "￥" + n.toLocaleString("zh-CN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  function formatPct(n) {
    if (n == null || isNaN(n)) return "—";
    return n.toFixed(1) + "%";
  }

  function formatDate(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (isNaN(d)) return iso.slice(0, 10);
    return d.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function getYearFromHash() {
    const m = location.hash.match(/^#(\d{4})$/);
    return m ? m[1] : null;
  }

  function setYearHash(year) {
    history.replaceState(null, "", "#" + year);
  }

  function setEmptyView(isEmpty) {
    document.getElementById("page-data").classList.toggle("hidden", isEmpty);
    document.getElementById("empty-inline").classList.toggle("hidden", !isEmpty);
  }

  function renderYearSwitcher(years, activeYear) {
    const nav = document.getElementById("year-switcher");
    nav.innerHTML = "";
    const keys = Object.keys(years).sort();

    if (keys.length <= 1) {
      nav.classList.add("hidden");
      return;
    }
    nav.classList.remove("hidden");

    keys.forEach(function (y) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "year-btn" + (y === activeYear ? " active" : "");
      btn.textContent = y;
      btn.dataset.year = y;
      btn.addEventListener("click", function () {
        renderYear(y);
      });
      nav.appendChild(btn);
    });
  }

  function renderKPIs(data) {
    document.getElementById("kpi-total-expense").textContent = formatMoney(data.total_expense);
    document.getElementById("kpi-total-income").textContent = formatMoney(data.total_income || 0);
    const nb = document.getElementById("kpi-net-balance");
    nb.textContent = formatMoney(data.net_balance || 0);
    nb.classList.toggle("kpi-negative", (data.net_balance || 0) < 0);
    document.getElementById("kpi-expense-ratio").textContent = formatPct(data.expense_ratio);
    document.getElementById("kpi-monthly-expense").textContent = formatMoney(
      data.monthly_avg_expense != null ? data.monthly_avg_expense : data.monthly_avg
    );
    document.getElementById("kpi-monthly-income").textContent = formatMoney(data.monthly_avg_income || 0);
  }

  function renderMonthly(data) {
    const chart = document.getElementById("monthly-chart");
    const tbody = document.querySelector("#monthly-table tbody");
    chart.innerHTML = "";
    tbody.innerHTML = "";

    const maxVal = Math.max.apply(
      null,
      data.months.flatMap(function (m) { return [m.income || 0, m.expense || 0]; }).concat([1])
    );

    document.getElementById("monthly-sub").textContent =
      currentYear + " 年 · 共 " + data.meta.months_with_data + " 个月有记录";

    data.months.forEach(function (m) {
      if (!m.has_data && !m.income && !m.expense) return;

      const incomePct = maxVal > 0 ? ((m.income || 0) / maxVal) * 100 : 0;
      const expensePct = maxVal > 0 ? ((m.expense || 0) / maxVal) * 100 : 0;

      const col = document.createElement("div");
      col.className = "month-col";
      col.innerHTML =
        '<div class="month-bar-group">' +
          '<div class="month-bar-wrap">' +
            '<div class="month-bar month-bar-income' + ((m.income || 0) === 0 ? " empty" : "") +
              '" style="height:' + Math.max(incomePct, (m.income || 0) > 0 ? 3 : 1) + '%"></div>' +
          '</div>' +
          '<div class="month-bar-wrap">' +
            '<div class="month-bar month-bar-expense' + ((m.expense || 0) === 0 ? " empty" : "") +
              '" style="height:' + Math.max(expensePct, (m.expense || 0) > 0 ? 3 : 1) + '%"></div>' +
          '</div>' +
        '</div>' +
        '<span class="month-amount">' + formatMoney(m.expense || 0) + "</span>" +
        '<span class="month-label">' + m.label + "</span>";
      chart.appendChild(col);

      const tr = document.createElement("tr");
      const balClass = (m.balance || 0) < 0 ? " amount-negative" : "";
      tr.innerHTML =
        "<td>" + m.label + "</td>" +
        '<td class="amount-cell amount-income">' + formatMoney(m.income || 0) + "</td>" +
        '<td class="amount-cell">' + formatMoney(m.expense || 0) + "</td>" +
        '<td class="amount-cell' + balClass + '">' + formatMoney(m.balance || 0) + "</td>" +
        "<td>" + formatPct(m.expense_ratio) + "</td>";
      tbody.appendChild(tr);
    });
  }

  function renderCategories(data) {
    const bars = document.getElementById("category-bars");
    const tbody = document.querySelector("#category-table tbody");
    bars.innerHTML = "";
    tbody.innerHTML = "";

    if (data.categories.length === 0) {
      bars.innerHTML = '<p class="panel-sub">暂无支出分类数据</p>';
      return;
    }

    data.categories.forEach(function (c) {
      const row = document.createElement("div");
      row.className = "cat-row";
      row.innerHTML =
        '<span class="cat-name">' + c.name + "</span>" +
        '<div class="cat-track"><div class="cat-fill" style="width:' + c.percent + '%"></div></div>' +
        '<span class="cat-pct">' + c.percent + "%</span>";
      bars.appendChild(row);

      const tr = document.createElement("tr");
      tr.innerHTML =
        "<td>" + c.name + "</td>" +
        '<td class="amount-cell">' + formatMoney(c.amount) + "</td>" +
        "<td>" + c.percent + "%</td>";
      tbody.appendChild(tr);
    });
  }

  function renderFootnote(data) {
    const meta = data.meta;
    const el = document.getElementById("footnote");
    el.textContent =
      "统计口径：支出占比 = 支出 ÷ 收入 × 100%；月均支出 = 总支出 ÷ 有记录月份（" +
      meta.months_with_data + " 个月）；月均收入 = 总收入 ÷ 有收入月份（" +
      (meta.months_with_income || 0) + " 个月）。";
  }

  function renderYear(year) {
    if (!dashboardData || !dashboardData.years[year]) {
      setEmptyView(true);
      return;
    }

    currentYear = year;
    setYearHash(year);

    const data = dashboardData.years[year];
    const isEmpty = data.meta.record_count === 0;

    document.title = "冰美式财务账本 · " + year;
    document.getElementById("updated-at").textContent =
      "数据更新于 " + formatDate(dashboardData.generated_at);
    document.getElementById("empty-year-label").textContent = year;

    renderYearSwitcher(dashboardData.years, year);

    if (isEmpty) {
      setEmptyView(true);
      return;
    }

    setEmptyView(false);
    renderKPIs(data);
    renderMonthly(data);
    renderCategories(data);
    renderFootnote(data);
  }

  function init() {
    fetch("./data.json")
      .then(function (res) {
        if (!res.ok) throw new Error("无法加载 data.json");
        return res.json();
      })
      .then(function (data) {
        dashboardData = data;
        document.getElementById("updated-at").textContent =
          "数据更新于 " + formatDate(data.generated_at);

        const hashYear = getYearFromHash();
        const defaultYear = String(data.default_year);
        const years = Object.keys(data.years);

        let startYear = defaultYear;
        if (hashYear && data.years[hashYear]) {
          startYear = hashYear;
        } else if (!data.years[defaultYear] && years.length > 0) {
          startYear = years[years.length - 1];
        }

        renderYear(startYear);
      })
      .catch(function (err) {
        document.getElementById("updated-at").textContent = "加载失败：" + err.message;
        console.error(err);
      });
  }

  window.addEventListener("hashchange", function () {
    const y = getYearFromHash();
    if (y && dashboardData && dashboardData.years[y]) {
      renderYear(y);
    }
  });

  init();
})();
