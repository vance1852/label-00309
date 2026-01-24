import request from "./request";

export const getSchedule = () => request.get("/schedule/");

export const updateSchedule = (data) => request.put("/schedule/", data);

export const runNow = () => request.post("/schedule/run-now/");
