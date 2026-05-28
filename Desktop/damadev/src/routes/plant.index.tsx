import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/plant/")({
  loader: () => {
    throw redirect({ to: "/plant/waves" });
  },
});
