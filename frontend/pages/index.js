import { useEffect } from "react";
import { useRouter } from "next/router";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = window.localStorage.getItem("medibot_token");
    router.replace(token ? "/chat" : "/login");
  }, [router]);

  return null;
}
