import axios from "axios";

import { supabase } from "../lib/supabase";

export const api = axios.create({
  baseURL: "/api"
});

api.interceptors.request.use(async (config) => {
  if (!supabase) {
    return config;
  }
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }

  return config;
});
