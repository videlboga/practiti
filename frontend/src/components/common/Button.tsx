import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({ children, ...props }) => (
  <button
    {...props}
    style={{
      padding: '10px 20px',
      borderRadius: 8,
      border: 'none',
      background: '#c7b299',
      color: '#fff',
      fontWeight: 600,
      fontSize: 16,
      boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
      cursor: 'pointer',
      ...props.style,
    }}
  >
    {children}
  </button>
);

export default Button; 