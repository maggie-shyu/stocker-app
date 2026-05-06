import { useEffect } from "react";

const NUMBER_INPUT_STYLE = `
  input[type="number"]::-webkit-outer-spin-button,
  input[type="number"]::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }

  input[type="number"] {
    -moz-appearance: textfield;
  }
`;

export function useInstallNumberInputStyles() {
  useEffect(() => {
    const style = document.createElement("style");
    style.textContent = NUMBER_INPUT_STYLE;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);
}
