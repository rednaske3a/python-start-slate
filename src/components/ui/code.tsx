
import { cn } from "@/lib/utils";

interface CodeProps {
  children: React.ReactNode;
  className?: string;
}

export function Code({ children, className }: CodeProps) {
  return (
    <pre className={cn("bg-gray-100 p-4 rounded-md overflow-x-auto", className)}>
      <code>{children}</code>
    </pre>
  );
}
