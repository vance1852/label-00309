import request from "./request";

export const getInspections = (params) =>
  request.get("/inspections/", { params });

export const getInspection = (id) => request.get(`/inspections/${id}/`);

export const deleteInspection = (id) => request.delete(`/inspections/${id}/`);

export const executeInspection = (data) =>
  request.post("/inspections/execute/", data);

export const getStatistics = () => request.get("/inspections/statistics/");
