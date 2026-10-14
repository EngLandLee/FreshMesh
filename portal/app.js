/*
 * SPDX-License-Identifier: Apache-2.0
 * Copyright 2026 FreshMesh-DXOS contributors
 */
(() => {
  "use strict";

  const state = {
    config: null,
    me: null,
    health: null,
    overview: null,
    recommendations: null,
    transfers: [],
    routes: [],
    drivers: [],
    currentTransfer: null,
    activeView: "overview",
    tokenTimer: null,
    transferFilter: "",
    transferSearch: "",
    lastRequest: 0,
  };
  const routeMap = new window.FreshMeshMap.RouteMap(document.querySelector("#route-map"));
  const statusNames = {
    submitted: "Chờ duyệt",
    approved: "Đã duyệt",
    rejected: "Từ chối",
    dispatched: "Đang giao",
    delivered: "Đã giao",
    received: "Đã nhận",
  };
  const actionNames = {
    created: "Tạo phiếu",
    submitted: "Gửi phê duyệt",
    approved: "Phê duyệt",
    rejected: "Từ chối",
    dispatched: "Điều phối",
    delivered: "Xác nhận giao",
    received: "Xác nhận nhận",
  };
  const roleNames = {
    owner: "Chủ chuỗi",
    store_manager: "Quản lý cửa hàng",
    driver: "Tài xế",
  };
  const api = "/api";
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [
    ...root.querySelectorAll(selector),
  ];
  const escapeHtml = (value) =>
    String(value ?? "").replace(
      /[&<>'"]/g,
      (char) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          "'": "&#39;",
          '"': "&quot;",
        })[char],
    );
  const formatNumber = (value) => Number(value || 0).toLocaleString("vi-VN");
  const formatCurrency = (value) => `${formatNumber(value)} ₫`;
  const formatDate = (value) =>
    value
      ? new Intl.DateTimeFormat("vi-VN", {
          dateStyle: "medium",
          timeStyle: "short",
        }).format(new Date(value))
      : "—";
  const formatShortDate = (value) =>
    value
      ? new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium" }).format(
          new Date(value),
        )
      : "—";
  const statusBadge = (status) =>
    `<span class="status-badge status-${escapeHtml(status)}">${escapeHtml(statusNames[status] || status || "Chưa rõ")}</span>`;
  const userScope = () =>
    state.me
      ? `${roleNames[state.me.role] || state.me.role} · ${state.me.chain_id || "—"}${state.me.store_id ? ` · ${state.me.store_id}` : ""}`
      : "—";

  function showToast(message, kind = "success") {
    const item = document.createElement("div");
    item.className = `toast toast-${kind}`;
    item.textContent = message;
    $("#toast-region").append(item);
    window.setTimeout(() => item.remove(), 5200);
  }
  function showGlobalError(message) {
    const el = $("#global-error");
    el.textContent = message;
    el.hidden = !message;
  }
  function setLoading(id, loading) {
    const el = $(`#${id}`);
    if (el) el.hidden = !loading;
  }
  function coreError(payload, fallback = "Không thể hoàn thành yêu cầu.") {
    return (
      payload?.error?.message_vi ||
      payload?.detail ||
      payload?.message ||
      fallback
    );
  }

  async function request(path, options = {}) {
    const headers = new Headers(options.headers || {});
    if (state.token) headers.set("Authorization", `Bearer ${state.token}`);
    if (options.body && !(options.body instanceof FormData))
      headers.set("Content-Type", "application/json");
    const response = await fetch(`${api}${path}`, { ...options, headers });
    if (response.status === 401) {
      clearSession();
      throw new Error("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
    }
    const type = response.headers.get("content-type") || "";
    const payload = type.includes("json")
      ? await response.json()
      : await response.text();
    if (!response.ok) {
      const error = new Error(coreError(payload));
      error.status = response.status;
      error.payload = payload;
      throw error;
    }
    return payload;
  }
  async function requestBlob(path) {
    const headers = state.token
      ? { Authorization: `Bearer ${state.token}` }
      : {};
    const response = await fetch(`${api}${path}`, { headers });
    if (response.status === 401) {
      clearSession();
      throw new Error("Phiên đăng nhập đã hết hạn.");
    }
    if (!response.ok) {
      let payload;
      try {
        payload = await response.json();
      } catch {
        payload = null;
      }
      throw new Error(coreError(payload, "Không thể tải tệp."));
    }
    return response.blob();
  }

  function randomString(bytes = 32) {
    const data = new Uint8Array(bytes);
    crypto.getRandomValues(data);
    return [...data].map((v) => v.toString(16).padStart(2, "0")).join("");
  }
  function base64Url(buffer) {
    return btoa(String.fromCharCode(...new Uint8Array(buffer)))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");
  }
  async function pkceChallenge(verifier) {
    return base64Url(
      await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier)),
    );
  }
  function clearSession() {
    sessionStorage.removeItem("fm_access_token");
    sessionStorage.removeItem("fm_token_exp");
    state.token = "";
    clearTimeout(state.tokenTimer);
  }
  function parseToken(token) {
    try {
      return JSON.parse(
        atob(
          token
            .split(".")[1]
            .replace(/-/g, "+")
            .replace(/_/g, "/")
            .padEnd(Math.ceil(token.split(".")[1].length / 4) * 4, "="),
        ),
      );
    } catch {
      return {};
    }
  }
  function scheduleExpiry(token) {
    const payload = parseToken(token);
    const expiry = Number(payload.exp || 0) * 1000;
    if (!expiry) return;
    const delay = Math.max(1000, expiry - Date.now() - 30000);
    state.tokenTimer = window.setTimeout(() => {
      showToast(
        "Phiên đăng nhập sắp hết hạn, đang đăng xuất an toàn.",
        "error",
      );
      clearSession();
      showAuth("Phiên đã hết hạn.");
    }, delay);
  }

  async function startLogin() {
    try {
      if (!state.config) state.config = await requestPublic("/config");
      const verifier = randomString(48);
      const stateValue = randomString(24);
      const challenge = await pkceChallenge(verifier);
      sessionStorage.setItem(
        "fm_oidc",
        JSON.stringify({ state: stateValue, verifier, created: Date.now() }),
      );
      const url = new URL(
        `${state.config.issuer}/protocol/openid-connect/auth`,
      );
      url.search = new URLSearchParams({
        client_id: state.config.client_id,
        redirect_uri: `${location.origin}/callback`,
        response_type: "code",
        scope: "openid profile",
        code_challenge: challenge,
        code_challenge_method: "S256",
        state: stateValue,
      }).toString();
      location.assign(url.toString());
    } catch (error) {
      showAuth(`Không thể khởi tạo đăng nhập: ${error.message}`);
    }
  }
  async function handleCallback() {
    const params = new URLSearchParams(location.search);
    const savedRaw = sessionStorage.getItem("fm_oidc");
    if (params.get("error")) {
      sessionStorage.removeItem("fm_oidc");
      showAuth(
        `Đăng nhập bị từ chối: ${params.get("error_description") || params.get("error")}`,
      );
      return true;
    }
    if (!params.get("code") || !savedRaw) return false;
    let saved;
    try {
      saved = JSON.parse(savedRaw);
    } catch {
      saved = null;
    }
    if (
      !saved ||
      saved.state !== params.get("state") ||
      Date.now() - Number(saved.created) > 10 * 60 * 1000
    ) {
      showAuth(
        "Phản hồi đăng nhập không hợp lệ hoặc đã hết hạn. Vui lòng thử lại.",
      );
      return true;
    }
    try {
      const response = await fetch(
        `${state.config.issuer}/protocol/openid-connect/token`,
        {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({
            grant_type: "authorization_code",
            client_id: state.config.client_id,
            redirect_uri: `${location.origin}/callback`,
            code: params.get("code"),
            code_verifier: saved.verifier,
          }),
        },
      );
      const payload = await response.json();
      if (!response.ok || !payload.access_token)
        throw new Error(
          payload.error_description || "Không nhận được access token.",
        );
      sessionStorage.removeItem("fm_oidc");
      state.token = payload.access_token;
      sessionStorage.setItem("fm_access_token", state.token);
      if (payload.expires_in)
        sessionStorage.setItem(
          "fm_token_exp",
          String(Date.now() + payload.expires_in * 1000),
        );
      scheduleExpiry(state.token);
      history.replaceState({}, "", "/");
      return true;
    } catch (error) {
      sessionStorage.removeItem("fm_oidc");
      showAuth(`Đăng nhập thất bại: ${error.message}`);
      return true;
    }
  }
  async function requestPublic(path) {
    const response = await fetch(`${api}${path}`);
    const payload = await response.json();
    if (!response.ok) throw new Error(coreError(payload));
    return payload;
  }
  function showAuth(message = "") {
    $("#auth-view").hidden = false;
    $("#app-view").hidden = true;
    $("#auth-status").textContent =
      message || "Đăng nhập để mở dữ liệu thuộc phạm vi của bạn.";
    $("#auth-status").className = message
      ? "notice notice-error"
      : "notice notice-neutral";
  }
  function showApp() {
    $("#auth-view").hidden = true;
    $("#app-view").hidden = false;
    $("#user-scope").textContent = userScope();
  }

  function setActiveView(view) {
    state.activeView = view;
    if (view !== "routes") routeMap.pause();
    $$(".view").forEach((el) => {
      el.hidden = el.id !== `view-${view}`;
    });
    $$(".nav-link").forEach((el) =>
      el.classList.toggle("is-active", el.dataset.nav === view),
    );
    $$(".nav-link").forEach((el) => el.setAttribute("aria-current", el.dataset.nav === view ? "page" : "false"));
    if (location.hash !== `#${view}`) history.replaceState({}, "", `#${view}`);
    if (view === "overview" && !state.overview) loadOverview();
    if (view === "recommendations" && !state.recommendations)
      loadRecommendations();
    if (
      (view === "transfers" || view === "delivery") &&
      !state.transfers.length
    )
      loadTransfers();
    if (view === "routes" && !state.routes.length) loadRoutes();
    if (view === "health" && !state.health) loadHealth();
  }
  function applyRoleVisibility() {
    const role = state.me?.role;
    const manager = role === "store_manager";
    const owner = role === "owner";
    const driver = role === "driver";
    $("#new-transfer-button").hidden = !manager;
    $("#plan-route-button").hidden = !owner;
    $("#nav-route-count").textContent = driver ? "" : "";
    if (driver) {
      $("#nav-overview-count").textContent = "";
      $("#nav-recommendation-count").textContent = "";
    }
  }

  async function loadOverview() {
    setLoading("overview-loading", true);
    $("#overview-content").hidden = true;
    try {
      state.overview = await request("/overview");
      renderOverview();
    } catch (error) {
      showGlobalError(error.message);
    } finally {
      setLoading("overview-loading", false);
    }
  }
  function renderOverview() {
    const data = state.overview || {};
    const counts = data.counts || {};
    $("#overview-content").hidden = false;
    showGlobalError("");
    [
      "submitted",
      "approved",
      "dispatched",
      "delivered",
      "received",
      "rejected",
    ].forEach((key) => {
      const el = $(`#count-${key}`);
      if (el) el.textContent = formatNumber(counts[key]);
    });
    $("#nav-transfer-count").textContent = counts.submitted
      ? formatNumber(counts.submitted)
      : "";
    $("#stock-table-body").innerHTML = (data.stock || [])
      .map(
        (item) =>
          `<tr><td><span class="table-primary">${escapeHtml(item.name || item.sku)}</span><span class="table-secondary">${escapeHtml(item.sku)} · <span title="${escapeHtml(item.lot_id)}">${escapeHtml(item.lot_id?.startsWith("received-") ? `Nhận ${item.lot_id.slice(9, 17)}` : item.lot_id)}</span></span></td><td>${escapeHtml(item.store_id)}</td><td class="numeric"><strong>${formatNumber(item.available)}</strong><span class="table-secondary">${formatNumber(item.quantity)} tổng · ${formatNumber(item.reserved)} giữ</span></td><td>${escapeHtml(formatShortDate(item.expires_on))}</td><td class="numeric">${formatCurrency(item.unit_cost_vnd)}</td></tr>`,
      )
      .join("");
    $("#stock-empty").hidden = Boolean((data.stock || []).length);
    $("#store-list").innerHTML = (data.stores || [])
      .map(
        (store) =>
          `<div class="store-item"><span class="store-pin" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 10V6l2-3h12l2 3v4M4 10v11h16V10M9 21v-7h6v7M3 10h18"/></svg></span><div><span class="store-name">${escapeHtml(store.name)}</span><span class="store-id">${escapeHtml(store.id)}</span></div><span class="store-coord">${Number(store.lat).toFixed(4)}, ${Number(store.lng).toFixed(4)}</span></div>`,
      )
      .join("");
    $("#store-empty").hidden = Boolean((data.stores || []).length);
    window.FreshMeshMap.overview($("#overview-map"), data.stores || []);
    $("#network-store-count").textContent = `${(data.stores || []).length} cửa hàng trong phạm vi`;
    routeMap.update({stores: data.stores || []});
    $("#stock-updated").textContent =
      `Cập nhật ${formatDate(new Date().toISOString())}`;
  }

  async function loadRecommendations() {
    setLoading("recommendations-loading", true);
    $("#recommendation-list").hidden = true;
    $("#recommendations-empty").hidden = true;
    try {
      state.recommendations = await request("/recommendations");
      const data = state.recommendations || {};
      const meta = $("#recommendations-meta");
      meta.innerHTML = `<strong>Phương pháp: ${escapeHtml(data.method || "Dịch vụ phân tích")}</strong><p>${escapeHtml(data.assumptions || "Giả định được trả về từ dịch vụ đề xuất.")}</p>`;
      meta.hidden = false;
      renderRecommendations();
    } catch (error) {
      showGlobalError(error.message);
    } finally {
      setLoading("recommendations-loading", false);
    }
  }
  function renderRecommendations() {
    const items = state.recommendations?.items || [];
    const list = $("#recommendation-list");
    list.innerHTML = items
      .map(
        (item, index) =>
          `<article class="recommendation-item"><div class="recommendation-kind">${escapeHtml(item.kind || "ĐỀ XUẤT")}<br>#${index + 1}</div><div><h2>${escapeHtml(item.name || item.sku || "Mặt hàng")}</h2><p class="recommendation-reason">${escapeHtml(item.reason || "Không có mô tả lý do.")}</p><div class="recommendation-meta"><span>Nguồn <strong>${escapeHtml(item.source_store_id || "—")}</strong></span><span>Đích <strong>${escapeHtml(item.target_store_id || "—")}</strong></span><span>Số lượng <strong>${formatNumber(item.quantity)}</strong></span><span>Dự báo <strong>${formatNumber(item.forecast_units)}</strong></span><span>Nguồn dữ liệu <strong>${escapeHtml(item.provenance || "API phân tích")}</strong></span></div></div><div class="recommendation-value"><strong>${formatCurrency(item.estimated_value_vnd)}</strong><span class="muted-label">giá trị ước tính</span><br><button class="button button-small button-primary" type="button" data-action="use-recommendation" data-index="${index}" ${state.me?.role !== "store_manager" ? "hidden" : ""}>Tạo phiếu</button></div></article>`,
      )
      .join("");
    list.hidden = !items.length;
    $("#recommendations-empty").hidden = Boolean(items.length);
  }

  async function loadTransfers() {
    setLoading("transfers-loading", true);
    $("#transfer-list").hidden = true;
    try {
      state.transfers = await request("/transfers");
      renderTransfers();
      renderDelivery();
      updateTransferOptions();
    } catch (error) {
      showGlobalError(error.message);
    } finally {
      setLoading("transfers-loading", false);
    }
  }
  function transferMatches(item) {
    const search = state.transferSearch.toLowerCase();
    return (
      (!state.transferFilter || item.status === state.transferFilter) &&
      (!search ||
        [
          item.id,
          item.sku,
          item.name,
          item.source_store_id,
          item.target_store_id,
        ].some((x) =>
          String(x || "")
            .toLowerCase()
            .includes(search),
        ))
    );
  }
  function renderTransfers() {
    const list = $("#transfer-list");
    const items = state.transfers.filter(transferMatches);
    list.innerHTML = items
      .map(
        (item) =>
          `<article class="transfer-item"><div><span class="transfer-id">${escapeHtml(item.id)}</span><p class="transfer-name">${escapeHtml(item.name || item.sku)} <span class="numeric">· ${formatNumber(item.quantity)} đơn vị</span></p><span class="transfer-date">Tạo ${escapeHtml(formatDate(item.created_at))}</span></div><div>${statusBadge(item.status)}</div><div class="transfer-route"><strong>${escapeHtml(item.source_store_id)}</strong><span class="transfer-arrow">→</span><strong>${escapeHtml(item.target_store_id)}</strong><span class="table-secondary">Tài xế: ${escapeHtml(item.driver_username || "Chưa phân công")}</span></div><button class="button button-small button-secondary" type="button" data-action="open-detail" data-id="${escapeHtml(item.id)}">Xem chi tiết</button></article>`,
      )
      .join("");
    list.hidden = !items.length;
    $("#transfers-empty").hidden = Boolean(items.length);
    $("#nav-transfer-count").textContent =
      state.transfers.filter((item) => item.status === "submitted").length ||
      "";
  }
  function renderDelivery() {
    const role = state.me?.role;
    const items = state.transfers.filter((item) =>
      role === "driver"
        ? ["dispatched"].includes(item.status)
        : role === "store_manager" && item.target_store_id === state.me.store_id && item.status === "delivered",
    );
    $("#delivery-list").innerHTML = items
      .map(
        (item) =>
          `<article class="delivery-item"><div class="delivery-info"><h2>${escapeHtml(item.name || item.sku)} · ${formatNumber(item.quantity)} đơn vị</h2><p>${escapeHtml(item.source_store_id)} → ${escapeHtml(item.target_store_id)} · ${escapeHtml(item.id)}</p>${statusBadge(item.status)}</div><div class="delivery-actions"><button class="button button-small button-secondary" type="button" data-action="open-detail" data-id="${escapeHtml(item.id)}">Chi tiết</button>${role === "driver" ? `<button class="button button-small button-primary" type="button" data-action="deliver" data-id="${escapeHtml(item.id)}">Xác nhận giao</button>` : `<button class="button button-small button-primary" type="button" data-action="receive" data-id="${escapeHtml(item.id)}">Xác nhận nhận</button>`}</div></article>`,
      )
      .join("");
    $("#delivery-empty").hidden = Boolean(items.length);
  }
  function updateTransferOptions() {
    const approved = state.transfers.filter(
      (item) => item.status === "approved",
    );
    $("#route-transfer-options").innerHTML = approved.length
      ? approved
          .map(
            (item) =>
              `<label><input type="checkbox" name="transfer_ids" value="${escapeHtml(item.id)}"><span>${escapeHtml(item.name || item.sku)} · ${escapeHtml(item.source_store_id)} → ${escapeHtml(item.target_store_id)} · ${formatNumber(item.quantity)}</span></label>`,
          )
          .join("")
      : '<p class="small-note">Chưa có phiếu đã duyệt.</p>';
  }

  async function loadRoutes() {
    setLoading("routes-loading", true);
    $("#route-list").hidden = true;
    try {
      state.routes = await request("/routes");
      if (!state.overview) await loadOverview();
      if (!state.transfers.length) await loadTransfers();
      renderRoutes();
    } catch (error) {
      showGlobalError(error.message);
    } finally {
      setLoading("routes-loading", false);
    }
  }
  function renderRoutes() {
    routeMap.update({routes: state.routes, stores: state.overview?.stores || [], transfers: state.transfers});
    const list = $("#route-list");
    list.innerHTML = state.routes
      .map(
        (route) =>
          `<article class="route-item"><div class="route-item-header"><div><h2>Lộ trình ${escapeHtml(route.id)}</h2><span class="muted-label">Tài xế: ${escapeHtml(route.driver_username)} · ${escapeHtml(route.status)}</span></div>${state.me?.role === "owner" && route.status === "planned" ? `<button class="button button-small button-primary" type="button" data-action="dispatch-route" data-id="${escapeHtml(route.id)}">Điều phối tuyến</button>` : ""}</div><div class="route-summary"><span>Khoảng cách <strong>${Number(route.distance_km || 0).toFixed(1)} km</strong></span><span>Phương pháp <strong>${escapeHtml(route.method || "—")}</strong></span><span>Phiếu <strong>${formatNumber((route.transfer_ids || []).length)}</strong></span></div><ol class="route-stops">${(route.stops || []).map((stop, index) => `<li class="route-stop"><span class="route-stop-number">ĐIỂM ${index + 1}</span><span class="route-stop-name">${escapeHtml(stop.name || stop.store_id)}</span><span class="route-stop-coord">${escapeHtml(stop.store_id)} · ${Number(stop.lat).toFixed(4)}, ${Number(stop.lng).toFixed(4)}</span></li>`).join("")}</ol><p class="small-note">${escapeHtml(route.assumptions || "Khoảng cách ước tính Haversine; không phải chỉ đường đường phố.")}</p></article>`,
      )
      .join("");
    list.hidden = !state.routes.length;
    $("#routes-empty").hidden = Boolean(state.routes.length);
  }
  async function loadHealth() {
    try {
      state.health = await request("/health");
      renderHealth();
    } catch (error) {
      showGlobalError(error.message);
    }
  }
  function renderHealth() {
    const services = state.health?.services || {};
    const cores = [
      { name: "Identity / SSO · Keycloak", ready: services.identity },
      { name: "API Gateway · APISIX", ready: services.gateway },
      {
        name: "Quản trị dữ liệu · PostgreSQL + SeaweedFS",
        ready: services.database && services.storage,
      },
      { name: "Workflow · Flowable BPMN", ready: services.workflow },
    ];
    $("#health-summary").textContent =
      `${cores.filter((core) => core.ready).length}/4 lõi sẵn sàng`;
    $("#service-health-list").innerHTML = cores
      .map(
        (core) =>
          `<div class="service-health ${core.ready ? "service-ok" : "service-fail"}"><span class="service-health-name">${core.name}</span><span class="service-health-state"><span class="status-dot" aria-hidden="true"></span>${core.ready ? "Sẵn sàng" : "Không khả dụng"}</span></div>`,
      )
      .join("");
  }

  function openDialog(id) {
    const dialog = $(`#${id}`);
    if (dialog && typeof dialog.showModal === "function") dialog.showModal();
    else dialog?.setAttribute("open", "");
  }
  function closeDialogs() {
    $$("dialog[open]").forEach((dialog) => dialog.close?.());
  }
  function fillFormData() {
    const allStores = state.overview?.stores || [];
    const managerStore =
      state.me?.role === "store_manager" ? state.me.store_id : "";
    const sourceStores = managerStore
      ? allStores.filter((store) => store.id === managerStore)
      : allStores;
    const sourceIds = new Set(sourceStores.map((store) => store.id));
    const targetStores = allStores.filter(
      (store) => !sourceIds.has(store.id) || !managerStore,
    );
    const stock = (state.overview?.stock || []).filter(
      (item) =>
        (!managerStore || item.store_id === managerStore) &&
        Number(item.available) > 0,
    );
    $("#form-source-store").innerHTML = sourceStores
      .map(
        (store) =>
          `<option value="${escapeHtml(store.id)}">${escapeHtml(store.id)} · ${escapeHtml(store.name)}</option>`,
      )
      .join("");
    $("#form-target-store").innerHTML = targetStores
      .map(
        (store) =>
          `<option value="${escapeHtml(store.id)}">${escapeHtml(store.id)} · ${escapeHtml(store.name)}</option>`,
      )
      .join("");
    $("#form-lot").innerHTML = stock
      .map(
        (item) =>
          `<option value="${escapeHtml(item.lot_id)}" data-store="${escapeHtml(item.store_id)}">${escapeHtml(item.name || item.sku)} · ${escapeHtml(item.lot_id)} · còn ${formatNumber(item.available)}</option>`,
      )
      .join("");
    const drivers = state.drivers || [];
    $("#form-driver").innerHTML = drivers
      .map(
        (driver) =>
          `<option value="${escapeHtml(driver.username)}">${escapeHtml(driver.name || driver.username)} · ${escapeHtml(driver.username)}</option>`,
      )
      .join("");
  }
  async function openTransferForm(recommendation = null) {
    if (!state.overview) await loadOverview();
    fillFormData();
    if (recommendation) {
      $("#form-source-store").value = recommendation.source_store_id || "";
      $("#form-target-store").value = recommendation.target_store_id || "";
      $("#form-lot").value = recommendation.lot_id || "";
      $("#form-quantity").value = recommendation.quantity || "";
    }
    $("#transfer-form-error").hidden = true;
    openDialog("transfer-dialog");
  }
  async function submitTransfer(event) {
    event.preventDefault();
    const form = new FormData(event.target);
    const errorEl = $("#transfer-form-error");
    errorEl.hidden = true;
    const button = event.target.querySelector('[type="submit"]');
    button.disabled = true;
    try {
      await request("/transfers", {
        method: "POST",
        body: JSON.stringify({
          source_store_id: form.get("source_store_id"),
          target_store_id: form.get("target_store_id"),
          lot_id: form.get("lot_id"),
          quantity: Number(form.get("quantity")),
          note: form.get("note") || "",
        }),
      });
      closeDialogs();
      showToast("Đã tạo phiếu và giữ tồn kho nguồn.");
      event.target.reset();
      state.transfers = [];
      state.overview = null;
      await Promise.all([loadOverview(), loadTransfers()]);
    } catch (error) {
      errorEl.textContent = error.message;
      errorEl.hidden = false;
    } finally {
      button.disabled = false;
    }
  }
  async function openRouteForm() {
    if (!state.drivers.length) {
      try {
        state.drivers = await request("/drivers");
      } catch (error) {
        showToast(error.message, "error");
        return;
      }
    }
    fillFormData();
    $("#route-form-error").hidden = true;
    openDialog("route-dialog");
  }
  async function submitRoute(event) {
    event.preventDefault();
    const form = new FormData(event.target);
    const ids = form.getAll("transfer_ids");
    if (!ids.length) {
      $("#route-form-error").textContent = "Chọn ít nhất một phiếu đã duyệt.";
      $("#route-form-error").hidden = false;
      return;
    }
    try {
      await request("/routes", {
        method: "POST",
        body: JSON.stringify({
          transfer_ids: ids,
          driver_username: form.get("driver_username"),
        }),
      });
      closeDialogs();
      showToast("Đã lập lộ trình.");
      state.routes = [];
      await loadRoutes();
    } catch (error) {
      $("#route-form-error").textContent = error.message;
      $("#route-form-error").hidden = false;
    }
  }

  async function openDetail(id) {
    try {
      const item = await request(`/transfers/${encodeURIComponent(id)}`);
      state.currentTransfer = item;
      renderDetail(item);
      openDialog("detail-dialog");
    } catch (error) {
      showToast(error.message, "error");
    }
  }
  function renderDetail(item) {
    $("#detail-dialog-title").textContent = `Phiếu ${item.id}`;
    const role = state.me?.role;
    let actions = "";
    if (role === "owner" && item.status === "submitted")
      actions += `<button class="button button-small button-primary" type="button" data-action="approve" data-id="${escapeHtml(item.id)}">Duyệt phiếu</button><button class="button button-small button-danger" type="button" data-action="reject" data-id="${escapeHtml(item.id)}">Từ chối</button>`;
    if (role === "owner" && item.status === "approved")
      actions += `<button class="button button-small button-primary" type="button" data-action="dispatch" data-id="${escapeHtml(item.id)}">Điều phối</button>`;
    if (role === "driver" && item.status === "dispatched")
      actions += `<button class="button button-small button-primary" type="button" data-action="deliver" data-id="${escapeHtml(item.id)}">Xác nhận giao</button>`;
    if (role === "store_manager" && item.target_store_id === state.me.store_id && item.status === "delivered")
      actions += `<button class="button button-small button-primary" type="button" data-action="receive" data-id="${escapeHtml(item.id)}">Xác nhận nhận</button>`;
    const docs = (item.documents || [])
      .map(
        (doc) =>
          `<div class="attachment"><span>${escapeHtml(doc.filename)} · ${formatNumber(doc.size)} bytes</span><button type="button" data-action="download-doc" data-transfer-id="${escapeHtml(item.id)}" data-doc-id="${escapeHtml(doc.id)}" data-filename="${escapeHtml(doc.filename)}">Tải xuống</button></div>`,
      )
      .join("");
    $("#transfer-detail-content").innerHTML =
      `<div class="detail-grid"><div class="detail-field"><span>Sản phẩm / SKU</span><strong>${escapeHtml(item.name || item.sku)}</strong></div><div class="detail-field"><span>Trạng thái</span><strong>${statusBadge(item.status)}</strong></div><div class="detail-field"><span>Tuyến</span><strong>${escapeHtml(item.source_store_id)} → ${escapeHtml(item.target_store_id)}</strong></div><div class="detail-field"><span>Số lượng yêu cầu</span><strong>${formatNumber(item.quantity)}</strong></div><div class="detail-field"><span>Giao thực tế</span><strong>${item.actual_quantity == null ? "—" : formatNumber(item.actual_quantity)}</strong></div><div class="detail-field"><span>Nhận thực tế</span><strong>${item.received_quantity == null ? "—" : formatNumber(item.received_quantity)}</strong></div><div class="detail-field"><span>Người tạo</span><strong>${escapeHtml(item.created_by)}</strong></div><div class="detail-field"><span>Tài xế</span><strong>${escapeHtml(item.driver_username || "Chưa phân công")}</strong></div></div><section class="detail-section"><h3>Nhật ký xử lý</h3><div class="timeline">${(item.events || []).map((event) => `<div class="timeline-event"><span class="timeline-action">${escapeHtml(actionNames[event.action] || event.action)}</span><span class="timeline-meta">${escapeHtml(event.actor)} · ${escapeHtml(formatDate(event.at))}</span>${event.note ? `<p class="timeline-note">${escapeHtml(event.note)}</p>` : ""}</div>`).join("") || '<p class="small-note">Chưa có sự kiện.</p>'}</div></section><section class="detail-section"><h3>Tài liệu bàn giao</h3><div class="attachment-list">${docs || '<p class="small-note">Chưa có tệp đính kèm.</p>'}</div><label class="upload-label" style="display:inline-grid;gap:6px;margin-top:12px;color:var(--ink-soft);font-size:12px;font-weight:700">Tải lên tài liệu<input id="document-upload" type="file" data-transfer-id="${escapeHtml(item.id)}"></label></section><div class="detail-actions">${actions}</div>`;
  }

  async function transition(id, path, body, success) {
    try {
      await request(`/transfers/${encodeURIComponent(id)}/${path}`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      showToast(success);
      closeDialogs();
      state.transfers = [];
      state.overview = null;
      await Promise.all([loadTransfers(), loadOverview()]);
      if (state.activeView === "delivery") renderDelivery();
    } catch (error) {
      showToast(error.message, "error");
    }
  }

  async function dispatchRoute(id) {
    if (
      !window.confirm(
        "Điều phối lộ trình sẽ thực hiện điều phối các phiếu trong tuyến và trừ tồn nguồn. Tiếp tục?",
      )
    )
      return;
    try {
      const route = await request(
        `/routes/${encodeURIComponent(id)}/dispatch`,
        { method: "POST" },
      );
      const failed = route.failures || [];
      showToast(
        failed.length
          ? `Đã điều phối một phần; ${failed.length} phiếu lỗi.`
          : "Đã điều phối lộ trình.",
      );
      state.routes = [];
      state.transfers = [];
      await Promise.all([loadRoutes(), loadTransfers(), loadOverview()]);
    } catch (error) {
      showToast(error.message, "error");
    }
  }
  async function promptTransition(kind, id) {
    const item =
      state.transfers.find((row) => row.id === id) || state.currentTransfer;
    const note = window.prompt(
      kind === "reject"
        ? "Lý do từ chối (bắt buộc):"
        : "Ghi chú (không bắt buộc):",
      "",
    );
    if (note === null) return;
    if (kind === "reject" && !note.trim()) {
      showToast("Cần ghi lý do từ chối.", "error");
      return;
    }
    if (kind === "approve" || kind === "reject")
      return transition(
        id,
        "approve",
        { decision: kind === "approve" ? "approved" : "rejected", note },
        kind === "approve"
          ? "Đã phê duyệt phiếu."
          : "Đã từ chối phiếu và giải phóng giữ hàng.",
      );
    if (kind === "dispatch") {
      const driver = window.prompt(
        "Tên đăng nhập tài xế được phân công:",
        item?.driver_username || "driver_a",
      );
      if (driver)
        return transition(
          id,
          "dispatch",
          { driver_username: driver.trim() },
          "Đã điều phối phiếu.",
        );
    }
    if (kind === "deliver" || kind === "receive") {
      const raw = window.prompt(
        `Số lượng ${kind === "deliver" ? "giao" : "nhận"} thực tế:`,
        String(
          kind === "receive"
            ? (item?.actual_quantity ?? 0)
            : (item?.quantity ?? 0),
        ),
      );
      if (raw === null) return;
      const quantity = Number(raw);
      if (!Number.isInteger(quantity) || quantity < 0) {
        showToast("Số lượng phải là số nguyên không âm.", "error");
        return;
      }
      return transition(
        id,
        kind,
        { actual_quantity: quantity, note },
        kind === "deliver"
          ? "Đã ghi nhận giao hàng."
          : "Đã xác nhận nhận hàng.",
      );
    }
  }
  async function uploadDocument(input) {
    const file = input.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      showToast("Tệp vượt giới hạn 5 MiB.", "error");
      input.value = "";
      return;
    }
    try {
      const form = new FormData();
      form.append("file", file);
      await request(
        `/transfers/${encodeURIComponent(input.dataset.transferId)}/documents`,
        { method: "POST", body: form },
      );
      showToast("Đã tải lên tài liệu.");
      await openDetail(input.dataset.transferId);
    } catch (error) {
      showToast(error.message, "error");
    }
    input.value = "";
  }
  async function downloadDocument(button) {
    try {
      const blob = await requestBlob(
        `/transfers/${encodeURIComponent(button.dataset.transferId)}/documents/${encodeURIComponent(button.dataset.docId)}`,
      );
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = button.dataset.filename || "document";
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      showToast(error.message, "error");
    }
  }
  async function askAgent(event) {
    event.preventDefault();
    const message = $("#agent-message").value.trim();
    if (!message) return;
    const response = $("#agent-response");
    response.innerHTML = "<p>Đang kết nối Ollama…</p>";
    try {
      const result = await request("/agent/chat", {
        method: "POST",
        body: JSON.stringify({ message }),
      });
      response.innerHTML = `<p>${escapeHtml(result.answer || "")}</p>${result.sources?.length ? `<p class="small-note">Nguồn: ${escapeHtml(result.sources.join(", "))} · Mô hình: ${escapeHtml(result.model || "—")}</p>` : ""}`;
    } catch (error) {
      response.innerHTML = `<p class="notice notice-error">Trợ lý hiện không khả dụng: ${escapeHtml(error.message)}</p>`;
    }
  }

  async function onAction(event) {
    const action = event.target.closest("[data-action]")?.dataset.action;
    if (!action) return;
    const target = event.target.closest("[data-action]");
    if (action === "open-route-view") return setActiveView("routes");
    if (action === "refresh-overview") {
      state.overview = null;
      return loadOverview();
    }
    if (action === "refresh-recommendations") {
      state.recommendations = null;
      return loadRecommendations();
    }
    if (action === "refresh-transfers") {
      state.transfers = [];
      return loadTransfers();
    }
    if (action === "refresh-health") {
      return loadHealth();
    }
    if (action === "open-transfer-form") return openTransferForm();
    if (action === "use-recommendation")
      return openTransferForm(
        state.recommendations.items[Number(target.dataset.index)],
      );
    if (action === "open-route-form") return openRouteForm();
    if (action === "open-detail") return openDetail(target.dataset.id);
    if (
      ["approve", "reject", "dispatch", "deliver", "receive"].includes(action)
    )
      return promptTransition(action, target.dataset.id);
    if (action === "dispatch-route") return dispatchRoute(target.dataset.id);
    if (action === "download-doc") return downloadDocument(target);
    if (action === "close-dialog") return closeDialogs();
    if (action === "open-agent") {
      $("#agent-response").innerHTML =
        "<p>Đặt câu hỏi về dữ liệu vận hành. Câu trả lời chỉ có sẵn khi Ollama đã được cấu hình.</p>";
      return openDialog("agent-dialog");
    }
  }

  async function bootstrap() {
    try {
      state.config = await requestPublic("/config");
    } catch (error) {
      showAuth(`Không thể kết nối cấu hình: ${error.message}`);
      return;
    }
    state.token = sessionStorage.getItem("fm_access_token") || "";
    if (
      state.token &&
      Number(sessionStorage.getItem("fm_token_exp") || 0) < Date.now()
    )
      clearSession();
    if (state.token) scheduleExpiry(state.token);
    const callback = await handleCallback();
    if (!state.token) {
      showAuth();
      return;
    }
    try {
      state.me = await request("/me");
      showApp();
      applyRoleVisibility();
      setActiveView(location.hash.slice(1) || "overview");
      loadHealth();
    } catch (error) {
      clearSession();
      showAuth(error.message);
    }
    if (callback && !state.token) showAuth();
  }

  document.addEventListener("click", (event) => {
    if (event.target.closest("#login-button")) startLogin();
    if (event.target.closest("#logout-button")) {
      clearSession();
      const redirect = `${location.origin}/`;
      const end = state.config?.issuer
        ? `${state.config.issuer}/protocol/openid-connect/logout?client_id=${encodeURIComponent(state.config.client_id)}&post_logout_redirect_uri=${encodeURIComponent(redirect)}`
        : redirect;
      location.assign(end);
    }
    if (event.target.closest("[data-nav]")) {
      const nav = event.target.closest("[data-nav]").dataset.nav;
      if (nav) setActiveView(nav);
    }
    onAction(event);
  });
  document.addEventListener("change", (event) => {
    if (event.target.matches("#document-upload")) uploadDocument(event.target);
    if (event.target.matches("#transfer-status-filter")) {
      state.transferFilter = event.target.value;
      renderTransfers();
    }
  });
  $("#transfer-search").addEventListener("input", (event) => {
    state.transferSearch = event.target.value;
    renderTransfers();
  });
  $("#transfer-form").addEventListener("submit", submitTransfer);
  $("#route-form").addEventListener("submit", submitRoute);
  $("#agent-form").addEventListener("submit", askAgent);
  window.addEventListener("hashchange", () => {
    const view = location.hash.slice(1);
    if ($(`#view-${view}`)) setActiveView(view);
  });
  bootstrap();
})();
