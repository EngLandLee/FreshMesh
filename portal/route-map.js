/*
 * SPDX-License-Identifier: Apache-2.0
 * Copyright 2026 FreshMesh-DXOS contributors
 * Offline schematic and presentation-only animation. No network or business writes.
 */
(() => {
  "use strict";
  const escape = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[char]);
  const icons = {
    play: '<path d="m8 5 11 7-11 7z"/>',
    pause: '<path d="M8 5v14M16 5v14"/>',
    reset: '<path d="M4 9a8 8 0 1 1 0 7M4 3v6h6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    minus: '<path d="M5 12h14"/>',
    fit: '<path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5"/>',
  };
  const icon = (name) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name]}</svg>`;
  const demoStops = [
    {id: "DEMO-01", name: "Điểm xuất minh họa", lat: 10.815, lng: 106.715},
    {id: "DEMO-02", name: "Cửa hàng minh họa 1", lat: 10.803, lng: 106.693},
    {id: "DEMO-03", name: "Cửa hàng minh họa 2", lat: 10.812, lng: 106.670},
    {id: "DEMO-04", name: "Cửa hàng minh họa 3", lat: 10.792, lng: 106.654},
  ];
  const validPoint = (point) => point.lat != null && point.lng != null && Number.isFinite(Number(point.lat)) && Number.isFinite(Number(point.lng)) && Math.abs(Number(point.lat)) <= 90 && Math.abs(Number(point.lng)) <= 180;

  // Deliberately schematic context: blocks, parks and waterways have no geographic claim.
  function ground() {
    let blocks = "";
    for (let row = 0; row < 6; row++) {
      for (let col = 0; col < 10; col++) {
        const x = col * 100 - 45 + (row % 2) * 12;
        const y = row * 83 - 26;
        const park = (row * 7 + col * 3) % 13 === 0;
        blocks += `<rect x="${x}" y="${y}" width="${72 + (col % 2) * 8}" height="58" rx="${park ? 12 : 5}" fill="${park ? "#cadcbd" : (row + col) % 3 === 0 ? "#e2e5da" : "#e8e9e0"}" stroke="${park ? "#b8cda9" : "#d8ddcf"}" stroke-width="1"/>`;
      }
    }
    return `<rect x="-900" y="-450" width="2700" height="1350" fill="#f1f1e8"/>
      <g transform="rotate(-12 450 225)" opacity=".88">${blocks}</g>
      <path d="M790-80C690 35 875 105 790 210S785 365 660 520" fill="none" stroke="#c0d9db" stroke-width="64"/>
      <path d="M790-80C690 35 875 105 790 210S785 365 660 520" fill="none" stroke="#d7e8e7" stroke-width="49"/>
      <g fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="m-30 295 210-60 170 15 260-95 330-25M155-40l80 170 100 170 50 200M-30 80l250 60 280-40 200 35 270 140" stroke="#d7d7c7" stroke-width="19"/>
        <path d="m-30 295 210-60 170 15 260-95 330-25M155-40l80 170 100 170 50 200M-30 80l250 60 280-40 200 35 270 140" stroke="#fffef8" stroke-width="13"/>
        <path d="M-30 390 240 340 510 370 920 310" stroke="#d7d7c7" stroke-width="12"/>
        <path d="M-30 390 240 340 510 370 920 310" stroke="#fffef8" stroke-width="8"/>
      </g>
      <g font-size="10" fill="#657568" letter-spacing="2" font-weight="600"><text x="76" y="85">KHU VỰC A</text><text x="365" y="407">KHU VỰC B</text><text x="640" y="57">KHU VỰC C</text></g>
      <text x="826" y="310" font-size="11" fill="#45696d" transform="rotate(-64 826 310)">Dòng nước minh họa</text>`;
  }
  function project(points) {
    if (!points.length) return [];
    const cosine = Math.cos(Number(points[0].lat) * Math.PI / 180);
    const xs = points.map((p) => Number(p.lng) * cosine);
    const ys = points.map((p) => Number(p.lat));
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const scale = Math.min(590 / (maxX - minX || .03), 230 / (maxY - minY || .03));
    return points.map((point, index) => ({...point, x: 430 + (xs[index] - (minX + maxX) / 2) * scale, y: 220 - (ys[index] - (minY + maxY) / 2) * scale}));
  }
  function markers(points, interactive, hasOrigin = false) {
    return points.map((point, index) => {
      const anchor = point.x > 650 ? "end" : "start";
      const tx = point.x + (anchor === "end" ? -23 : 23);
      return `<g class="map-marker${index === 0 && hasOrigin ? " map-origin" : ""}" ${interactive ? `role="button" tabindex="0" data-map-stop="${index}" aria-label="Chọn ${escape(point.name || point.id)}"` : ""}>
        <circle cx="${point.x}" cy="${point.y}" r="21" fill="#fff" opacity=".72"/>
        <circle cx="${point.x}" cy="${point.y}" r="14" fill="${index === 0 && hasOrigin ? "#154b3a" : "#fff"}" stroke="#154b3a" stroke-width="2.5"/>
        <text x="${point.x}" y="${point.y + 4}" text-anchor="middle" font-size="11" font-weight="700" fill="${index === 0 && hasOrigin ? "#fff" : "#154b3a"}">${interactive && hasOrigin ? index === 0 ? "S" : index : index + 1}</text>
        <text class="map-point-label" x="${tx}" y="${point.y - 8}" text-anchor="${anchor}" font-size="12" font-weight="700" fill="#173c2d" paint-order="stroke" stroke="#f7f8f0" stroke-width="5" stroke-linejoin="round">${escape(point.name?.replace("Mini-mart ", "") || point.id)}</text>
        <text x="${tx}" y="${point.y + 9}" text-anchor="${anchor}" font-size="10" fill="#48624c" paint-order="stroke" stroke="#f7f8f0" stroke-width="4">${escape(point.id)}</text>
      </g>`;
    }).join("");
  }
  const compass = '<g transform="translate(851 43)"><circle r="22" fill="#fff"/><path d="m0-13-5 17 5-3 5 3z" fill="#315b48"/><text y="-29" text-anchor="middle" font-size="10" fill="#315b48" font-weight="700">BẮC</text></g>';

  class RouteMap {
    constructor(root) {
      this.root = root;
      this.routes = [];
      this.stores = [];
      this.transfers = [];
      this.progress = 0;
      this.playing = false;
      this.zoom = 1;
      this.reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
      root.innerHTML = `<div class="map-workspace-heading"><div><h2>Bản đồ điều phối</h2><p>Khám phá tuyến và trình diễn thứ tự giao hàng.</p></div><span class="simulation-tag"><span aria-hidden="true"></span>Mô phỏng · không phải GPS</span></div>
        <div class="map-layout"><div class="map-stage"><div class="map-canvas"><svg id="map-svg" viewBox="0 0 900 450" role="group" aria-label="Sơ đồ tuyến giao hàng; nền đường phố và sông chỉ minh họa"></svg>
          <div class="map-zoom" role="group" aria-label="Thu phóng bản đồ"><button id="map-zoom-in" type="button" aria-label="Phóng to">${icon("plus")}</button><button id="map-zoom-out" type="button" aria-label="Thu nhỏ">${icon("minus")}</button><button id="map-fit" type="button" aria-label="Vừa khung">${icon("fit")}</button></div>
          <span class="map-attribution">SƠ ĐỒ MINH HỌA · KHÔNG DẪN ĐƯỜNG</span></div>
          <div class="map-transport"><button id="map-play" class="button button-primary" type="button" aria-pressed="false">${icon("play")}<span>Chạy mô phỏng</span></button><button id="map-reset" class="map-reset" type="button" aria-label="Đặt lại mô phỏng">${icon("reset")}</button><div class="map-progress-wrap"><div><span id="map-status" role="status">Sẵn sàng mô phỏng</span><span id="map-percent">0%</span></div><progress id="map-progress" max="100" value="0" aria-label="Tiến độ mô phỏng"></progress></div><label class="map-speed">Tốc độ<select id="map-speed" aria-label="Tốc độ mô phỏng"><option value="1">1×</option><option value="2">2×</option><option value="4">4×</option></select></label></div>
        </div><aside class="map-itinerary"><label class="map-route-label" for="map-route-select">Tuyến đang xem</label><select id="map-route-select"><option value="">Tuyến minh họa · không lưu hệ thống</option></select><p id="map-source" class="map-source"></p><ol id="map-stop-list" class="map-stop-list"></ol><div id="map-selected-stop" class="map-selected-stop" aria-live="polite"></div></aside></div>
        <p class="map-disclaimer">Vị trí cửa hàng lấy từ dữ liệu được cấp quyền khi chọn tuyến hệ thống. Nền địa lý chỉ là sơ đồ; đường nối và chuyển động không phải đường đi thực tế, GPS hay thời gian đến dự kiến.</p>`;
      this.svg = root.querySelector("#map-svg");
      root.querySelector("#map-route-select").addEventListener("change", () => this.render());
      root.querySelector("#map-play").addEventListener("click", () => this.playing ? this.pause() : this.play());
      root.querySelector("#map-reset").addEventListener("click", () => this.reset());
      root.querySelector("#map-zoom-in").addEventListener("click", () => this.setZoom(this.zoom + .25));
      root.querySelector("#map-zoom-out").addEventListener("click", () => this.setZoom(this.zoom - .25));
      root.querySelector("#map-fit").addEventListener("click", () => this.setZoom(1));
      root.addEventListener("click", (event) => {
        const stop = event.target.closest("[data-map-stop]");
        if (stop) this.selectStop(Number(stop.dataset.mapStop));
      });
      this.svg.addEventListener("keydown", (event) => {
        const stop = event.target.closest("[data-map-stop]");
        if (stop && (event.key === "Enter" || event.key === " ")) {event.preventDefault(); this.selectStop(Number(stop.dataset.mapStop));}
      });
      document.addEventListener("visibilitychange", () => {if (document.hidden) this.pause();});
      this.render();
    }
    update({routes = this.routes, stores = this.stores, transfers = this.transfers}) {
      this.routes = routes; this.stores = stores; this.transfers = transfers;
      const select = this.root.querySelector("#map-route-select");
      const selected = select.value;
      select.innerHTML = '<option value="">Tuyến minh họa · không lưu hệ thống</option>' + routes.map((route) => `<option value="${escape(route.id)}">${escape(route.id.slice(0, 8))} · ${escape(route.driver_username || "Chưa có tài xế")}</option>`).join("");
      select.value = routes.some((route) => route.id === selected) ? selected : "";
      this.render();
    }
    render() {
      this.pause(); this.progress = 0;
      const id = this.root.querySelector("#map-route-select").value;
      const route = this.routes.find((item) => item.id === id);
      let points;
      let sourceMessage;
      if (route) {
        const routeTransfers = this.transfers.filter((item) => (route.transfer_ids || []).includes(item.id));
        const sourceIds = [...new Set(routeTransfers.map((item) => item.source_store_id))];
        const source = sourceIds.length === 1 ? this.stores.find((store) => store.id === sourceIds[0]) : null;
        const stops = (route.stops || []).map((stop) => ({...stop, id: stop.store_id}));
        points = [...(source && validPoint(source) ? [source] : []), ...stops].filter(validPoint);
        this.hasOrigin = Boolean(source && validPoint(source));
        const distance = Number(route.distance_km);
        const distanceLabel = Number.isFinite(distance) ? `${distance.toLocaleString("vi-VN", {maximumFractionDigits: 1})} km ước tính` : "Khoảng cách chưa có";
        sourceMessage = `Tuyến hệ thống · ${distanceLabel} · ${route.method || "Phương pháp chưa rõ"}. ${this.hasOrigin ? "Thứ tự điểm từ API; chuyển động chỉ minh họa." : "Chưa đủ dữ liệu điểm xuất; chỉ hiển thị các điểm giao có tọa độ."}`;
      } else {
        points = demoStops; this.hasOrigin = true;
        sourceMessage = "Tuyến minh họa độc lập. 4 điểm giả lập để trình diễn, không phải cửa hàng hoặc phiếu chuyển trong hệ thống.";
      }
      this.points = project(points);
      this.root.querySelector("#map-source").textContent = sourceMessage;
      this.root.querySelector("#map-source").classList.toggle("is-demo", !route);
      const line = this.points.map((point) => `${point.x},${point.y}`).join(" ");
      this.svg.innerHTML = `<title>${route ? "Tuyến hệ thống trên nền sơ đồ" : "Tuyến minh họa độc lập"}</title>${ground()}${this.points.length > 1 ? `<polyline points="${line}" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/><polyline id="map-route-line" points="${line}" fill="none" stroke="#31795a" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><polyline points="${line}" fill="none" stroke="#b7dfab" stroke-width="1.5" stroke-dasharray="2 12"/>` : ""}${markers(this.points, true, this.hasOrigin)}${compass}${this.points.length > 1 ? '<g id="map-vehicle" aria-label="Xe mô phỏng"><circle r="24" fill="#164b39" fill-opacity=".12"/><rect x="-17" y="-13" width="34" height="27" rx="8" fill="#154b3a" stroke="#fff" stroke-width="3"/><path d="M-10-6H2v12h-12zM2-2h5l4 5v3H2" fill="none" stroke="#fff" stroke-width="1.5"/><circle cx="-6" cy="7" r="2" fill="#fff"/><circle cx="7" cy="7" r="2" fill="#fff"/></g>' : ""}`;
      this.root.querySelector("#map-stop-list").innerHTML = this.points.length ? this.points.map((point, index) => `<li><button type="button" data-map-stop="${index}" aria-pressed="false"><span class="stop-index">${index === 0 && this.hasOrigin ? "S" : index + (this.hasOrigin ? 0 : 1)}</span><span><strong>${escape(point.name || point.id)}</strong><small>${index === 0 && this.hasOrigin ? "Điểm xuất phát" : "Điểm giao"} · ${escape(point.id)}</small></span></button></li>`).join("") : '<li class="map-no-stops">Chưa có tọa độ hợp lệ để hiển thị.</li>';
      this.root.querySelector("#map-play").disabled = this.points.length < 2;
      this.setZoom(1); this.setProgress(0); this.selectStop(0);
    }
    selectStop(index) {
      const point = this.points[index];
      if (!point) {this.root.querySelector("#map-selected-stop").textContent = "Không có điểm để mô phỏng.";return;}
      this.root.querySelectorAll("[data-map-stop]").forEach((element) => {
        const selected = Number(element.dataset.mapStop) === index;
        element.classList.toggle("is-selected", selected);
        element.setAttribute("aria-pressed", String(selected));
      });
      this.root.querySelector("#map-selected-stop").innerHTML = `<span>Điểm đang chọn</span><strong>${escape(point.name || point.id)}</strong><small>${Number(point.lat).toFixed(4)}° B · ${Number(point.lng).toFixed(4)}° Đ</small>`;
    }
    setZoom(value) {
      this.zoom = Math.max(1, Math.min(2.5, value));
      const width = 900 / this.zoom, height = 450 / this.zoom;
      this.svg.setAttribute("viewBox", `${(900 - width) / 2} ${(450 - height) / 2} ${width} ${height}`);
      this.root.querySelector("#map-zoom-in").disabled = this.zoom >= 2.5;
      this.root.querySelector("#map-zoom-out").disabled = this.zoom <= 1;
    }
    setProgress(value) {
      this.progress = Math.max(0, Math.min(100, value));
      this.root.querySelector("#map-progress").value = this.progress;
      this.root.querySelector("#map-percent").textContent = `${Math.floor(this.progress)}%`;
      if (this.points.length < 2) {this.root.querySelector("#map-status").textContent = "Cần ít nhất 2 điểm có tọa độ";return;}
      const vehicle = this.root.querySelector("#map-vehicle");
      const rawPosition = this.progress / 100 * (this.points.length - 1);
      const position = this.reducedMotion.matches ? Math.floor(rawPosition) : rawPosition;
      const segment = Math.min(this.points.length - 2, Math.floor(position));
      const fraction = position - segment;
      const a = this.points[segment], b = this.points[segment + 1];
      vehicle.setAttribute("transform", `translate(${a.x + (b.x - a.x) * fraction} ${a.y + (b.y - a.y) * fraction})`);
      this.root.querySelector("#map-status").textContent = this.progress === 100 ? "Đã hoàn tất mô phỏng" : this.progress === 0 ? "Sẵn sàng mô phỏng" : `${this.playing ? "Đang mô phỏng" : "Đã tạm dừng"} · chặng ${Math.min(this.points.length - 1, Math.floor(rawPosition) + 1)}/${this.points.length - 1}`;
      this.root.querySelectorAll("#map-stop-list li").forEach((item, index) => item.classList.toggle("is-passed", rawPosition >= index));
    }
    play() {
      if (this.points.length < 2) return;
      if (this.progress >= 100) this.setProgress(0);
      this.playing = true;
      this.root.querySelector("#map-play").innerHTML = `${icon("pause")}<span>Tạm dừng</span>`;
      this.root.querySelector("#map-play").setAttribute("aria-pressed", "true");
      let previous = performance.now();
      const tick = (now) => {
        if (!this.playing) return;
        const elapsed = Math.min(now - previous, 100); previous = now;
        const speed = Number(this.root.querySelector("#map-speed").value);
        this.setProgress(this.progress + elapsed / 180 * speed);
        if (this.progress >= 100) {this.pause();this.selectStop(this.points.length - 1);return;}
        this.frame = requestAnimationFrame(tick);
      };
      this.frame = requestAnimationFrame(tick);
    }
    pause() {
      this.playing = false; cancelAnimationFrame(this.frame);
      this.root.querySelector("#map-play").innerHTML = `${icon("play")}<span>Chạy mô phỏng</span>`;
      this.root.querySelector("#map-play").setAttribute("aria-pressed", "false");
      if (this.points) this.setProgress(this.progress);
    }
    reset() {this.pause(); this.setProgress(0); this.selectStop(0);}
  }
  function overview(root, stores) {
    const points = project(stores.filter(validPoint));
    root.innerHTML = `<svg viewBox="0 0 900 450" role="img" aria-label="${points.length} cửa hàng có tọa độ, trên nền bản đồ sơ đồ"><title>Mạng lưới cửa hàng trong phạm vi tài khoản</title>${ground()}${markers(points, false)}${compass}</svg><span class="map-attribution">NỀN SƠ ĐỒ · VỊ TRÍ TỪ HỆ THỐNG</span>${points.length ? "" : '<p class="map-empty-overlay">Chưa có tọa độ cửa hàng trong phạm vi.</p>'}`;
  }
  window.FreshMeshMap = {RouteMap, overview};
})();
