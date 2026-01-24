import request from "./request";

export const login = (data) => request.post("/auth/login/", data);

export const logout = () => request.post("/auth/logout/");

export const getProfile = () => request.get("/auth/profile/");

export const changePassword = (data) => request.put("/auth/password/", data);
