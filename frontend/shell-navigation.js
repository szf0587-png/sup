"use strict";

/* One navigation definition is shared by every console page. */
(function () {
    const items = [
        { href: "index.html", label: "评估工作台", note: "LAND WORKSPACE", icon: "fa-map-location-dot" },
        { href: "data-center.html", label: "项目数据", note: "PROJECT DATA", icon: "fa-database" },
        { href: "iserver-tools.html", label: "空间分析", note: "SPATIAL ANALYSIS", icon: "fa-draw-polygon" },
        { href: "map3d.html", label: "三维场景", note: "3D REALSPACE", icon: "fa-cube" },
        { href: "golden_standard.html", label: "模型库", note: "MODEL LIBRARY", icon: "fa-scale-balanced" },
        { href: "ai-chat.html", label: "AI 助手", note: "DECISION AGENT", icon: "fa-comments" },
    ];

    const currentPage = window.location.pathname.split("/").pop() || "index.html";
    const currentItem = items.find((item) => item.href === currentPage) || items[0];
    const navigation = document.createElement("aside");
    navigation.className = "app-navigation";
    navigation.setAttribute("aria-label", "平台导航");
    navigation.innerHTML = `
        <a class="app-navigation__brand" href="index.html" aria-label="天眼寻珍工作台">
            <span class="app-navigation__brand-mark"><i class="fa-solid fa-layer-group" aria-hidden="true"></i></span>
            <span><strong>天眼寻珍</strong><small>LAND INTELLIGENCE</small></span>
        </a>
        <p class="app-navigation__section">工作空间</p>
        <nav class="app-navigation__list">${items.map((item) => `
            <a class="app-navigation__link" href="${item.href}" title="${item.label}"${item.href === currentPage ? ' aria-current="page"' : ""}>
                <i class="fa-solid ${item.icon}" aria-hidden="true"></i>
                <span><b>${item.label}</b><small>${item.note}</small></span>
            </a>
        `).join("")}</nav>
        <div class="app-navigation__foot"><span></span><small>${currentItem.label}</small></div>
    `;

    document.body.classList.add("has-app-navigation");
    document.body.dataset.consolePage = currentPage.replace(".html", "");
    document.body.insertBefore(navigation, document.body.firstChild);
})();
