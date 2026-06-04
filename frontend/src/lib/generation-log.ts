type LogStep =
  | "start"
  | "translate"
  | "translated"
  | "request"
  | "created"
  | "poll"
  | "completed"
  | "download"
  | "share"
  | "error";

const LOG_PREFIX = "[Studio]";

export function logGeneration(step: LogStep, detail?: unknown) {
  const ts = new Date().toISOString();
  const detailStr = detail !== undefined ? JSON.stringify(detail, null, 2) : "";
  if (step === "error") {
    console.error(`${LOG_PREFIX} ${ts} [${step.toUpperCase()}]`, detailStr);
  } else {
    console.log(`${LOG_PREFIX} ${ts} [${step.toUpperCase()}]`, detailStr);
  }
}
