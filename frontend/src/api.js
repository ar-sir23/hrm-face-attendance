import axios from "axios";

const API = axios.create({ baseURL: "/api" });

export const getToday        = ()          => API.get("/attendance/today");
export const getTodayDetails = ()          => API.get("/attendance/today/details");
export const getTodayLogs    = ()          => API.get("/attendance/logs/today");
export const getEmployees    = ()          => API.get("/employees/");
export const getDepartments  = ()          => API.get("/employees/departments");
export const getCameraStatus = ()          => API.get("/camera/status");
export const getLateToday    = ()          => API.get("/attendance/report/late-today");
export const createEmployee  = (data)      => API.post("/employees/", data);
export const createDepartment= (data)      => API.post("/employees/departments", data);
export const manualPunch     = (data)      => API.post("/attendance/manual-punch", data);

export const registerFace = (id, file) => {
  const form = new FormData();
  form.append("file", file);
  return API.post("/employees/" + id + "/register-face", form);
};

export const facePunch = (file, location) => {
  const form = new FormData();
  form.append("file", file);
  form.append("location", location || "Main Gate");
  return API.post("/attendance/face-punch", form);
};
