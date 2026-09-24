"use client";

import React, {
  useRef,
  useState,
  useImperativeHandle,
  forwardRef,
  ReactNode,
} from "react";
import { AlertCircle } from "lucide-react";

export interface InputShakeHandle {
  trigger: (customMessage?: string) => void;
  cancel: () => void;
}

interface InputShakeProps {
  children: ReactNode;
  message?: string;
  className?: string;
  wrapClassName?: string;
  onCancel?: () => void;
}

function readMs(name: string, fallback: number): number {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return fallback;
  }
  const raw = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  const n = parseFloat(raw);
  return Number.isFinite(n) ? n : fallback;
}

export const InputShake = forwardRef<InputShakeHandle, InputShakeProps>(
  function InputShake(
    { children, message = "This field is required", className = "", wrapClassName = "", onCancel },
    ref
  ) {
    const inputRef = useRef<HTMLDivElement>(null);
    const timerRef = useRef<number | null>(null);
    const [error, setError] = useState(false);
    const [activeMessage, setActiveMessage] = useState(message);

    const trigger = (customMessage?: string) => {
      if (customMessage) {
        setActiveMessage(customMessage);
      } else {
        setActiveMessage(message);
      }

      setError(true);

      if (inputRef.current) {
        inputRef.current.classList.remove("is-shaking");
        void inputRef.current.offsetWidth;
        inputRef.current.classList.add("is-shaking");
      }

      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
      }

      const shakeMs =
        readMs("--shake-dur-a", 80) * 2 + readMs("--shake-dur-b", 60) * 2;
      const hold = readMs("--revert-hold", 3000);

      timerRef.current = window.setTimeout(() => {
        setError(false);
        timerRef.current = null;
      }, shakeMs + hold);
    };

    const cancel = () => {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      setError(false);
      onCancel?.();
    };

    useImperativeHandle(ref, () => ({
      trigger,
      cancel,
    }));

    return (
      <div className={`t-input-wrap ${error ? "is-error" : ""} ${wrapClassName}`}>
        <div
          ref={inputRef}
          className={`t-input ${error ? "is-error" : ""} ${className}`}
          onInput={cancel}
        >
          {children}
        </div>
        <p className="t-error-msg">
          <AlertCircle className="w-3.5 h-3.5 shrink-0 inline-block" />
          <span>{activeMessage}</span>
        </p>
      </div>
    );
  }
);
