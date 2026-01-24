import request from "./request";

export const getServers = (params) => request.get("/servers/", { params });

export const getServer = (id) => request.get(`/servers/${id}/`);

export const createServer = (data) => request.post("/servers/", data);

export const updateServer = (id, data) => request.put(`/servers/${id}/`, data);

export const deleteServer = (id) => request.delete(`/servers/${id}/`);

export const testServer = (id) => request.post(`/servers/${id}/test/`);

export const getActiveServers = () => request.get("/servers/active/");
