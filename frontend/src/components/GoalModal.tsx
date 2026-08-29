import React from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/Card";

type GoalModalProps = {
  open: boolean;
  onClose: () => void;
  options: { label: string; value: string }[];
  onSelect: (value: string) => void;
  title: string;
};

const GoalModal: React.FC<GoalModalProps> = ({
  open,
  onClose,
  options,
  onSelect,
  title,
}) => {
  if (!open) return null;

  return (
    // Backdrop and spacing come from tokens now; this used to carry its own
    // inline `rgba(0,0,0,0.5)` and per-button margins.
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-overlay p-4"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onClick={onClose}
    >
      <Card
        className="w-full max-w-sm p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-heading">{title}</h2>
        <div className="flex flex-col gap-2">
          {options.map((opt) => (
            <Button key={opt.value} onClick={() => onSelect(opt.value)}>
              {opt.label}
            </Button>
          ))}
        </div>
        <Button variant="neutral" onClick={onClose}>
          Cancel
        </Button>
      </Card>
    </div>
  );
};

export default GoalModal;
