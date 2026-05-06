import { useEffect, useState } from "react";

function getPageSize() {
  if (typeof window === "undefined") {
    return 25;
  }
  return window.innerWidth >= 1024 ? 25 : 10;
}

export function useResponsivePageSize() {
  const [pageSize, setPageSize] = useState(getPageSize);

  useEffect(() => {
    const handleResize = () => {
      setPageSize(getPageSize());
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return pageSize;
}
