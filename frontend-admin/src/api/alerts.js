import request from "./request";

export const getAlertConfig = () => request.get("/alerts/config/");

export const updateAlertConfig = (data) => request.put("/alerts/config/", data);

export const sendTestEmail = (data) => request.post("/alerts/test/", data);

export const getRecipients = () => request.get("/alerts/recipients/");

export const createRecipient = (data) =>
  request.post("/alerts/recipients/", data);

export const updateRecipient = (id, data) =>
  request.put(`/alerts/recipients/${id}/`, data);

export const deleteRecipient = (id) =>
  request.delete(`/alerts/recipients/${id}/`);
