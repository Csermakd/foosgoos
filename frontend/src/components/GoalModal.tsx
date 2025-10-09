import React from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/button';

type GoalModalProps = {
  open: boolean;
  onClose: () => void;
  options: { label: string; value: string }[];
  onSelect: (value: string) => void;
  title: string;
};

const GoalModal: React.FC<GoalModalProps> = ({ open, onClose, options, onSelect, title }) => {
  if (!open) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0, left: 0, right: 0, bottom: 0,
        background: 'rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
    >
      <Card>
        <h2>{title}</h2>
        {options.map(opt => (
          <Button key={opt.value} onClick={() => onSelect(opt.value)} style={{ margin: '0.5rem 0' }}>
            {opt.label}
          </Button>
        ))}
        <Button onClick={onClose} style={{ marginTop: '1rem' }}>Cancel</Button>
      </Card>
    </div>
  );
};

export default GoalModal;

