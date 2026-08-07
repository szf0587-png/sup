"use strict";

(function () {
    const items = [
        { href: "index.html", label: "土地资源工作台", icon: "fa-map-location-dot" },
        { href: "data-center.html", label: "项目数据", icon: "fa-database" },
        { href: "iserver-tools.html", label: "空间分析", icon: "fa-draw-polygon" },
        { href: "map3d.html", label: "三维场景", icon: "fa-cube" },
        { href: "golden_standard.html", label: "模型库", icon: "fa-scale-balanced" },
        { href: "ai-chat.html", label: "AI 助手", icon: "fa-comments" },
    ];

    const currentPage = window.location.pathname.split("/").pop() || "index.html";
    const navigation = document.createElement("aside");
    navigation.className = "app-navigation";
    navigation.setAttribute("aria-label", "主导航");
    navigation.innerHTML = `
        <div class="app-navigation__brand" aria-hidden="true"><i class="fa-solid fa-layer-group"></i></div>
        <nav class="app-navigation__list">${items.map((item) => `
            <a class="app-navigation__link" href="${item.href}" title="${item.label}" aria-label="${item.label}"${item.href === currentPage ? ' aria-current="page"' : ""}>
                <i class="fa-solid ${item.icon}" aria-hidden="true"></i>
            </a>
        `).join("")}</nav>
    `;

    document.body.classList.add("has-app-navigation");
    document.body.insertBefore(navigation, document.body.firstChild);
})();
