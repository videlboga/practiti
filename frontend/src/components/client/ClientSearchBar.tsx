import React from 'react';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import SearchIcon from '@mui/icons-material/Search';

interface ClientSearchBarProps {
  value: string;
  onChange: (value: string) => void;
}

const ClientSearchBar: React.FC<ClientSearchBarProps> = ({ value, onChange }) => (
  <TextField
    variant="outlined"
    placeholder="Поиск клиентов"
    value={value}
    onChange={e => onChange(e.target.value)}
    fullWidth
    sx={{
      bgcolor: 'grey.100',
      borderRadius: 2,
      mb: 2,
      '& .MuiOutlinedInput-root': {
        borderRadius: 2,
        background: 'inherit',
      },
      input: { fontSize: 16 },
    }}
    InputProps={{
      startAdornment: (
        <InputAdornment position="start">
          <SearchIcon sx={{ color: 'grey.400' }} />
        </InputAdornment>
      ),
    }}
    inputProps={{ 'aria-label': 'Поиск клиентов' }}
  />
);

export default ClientSearchBar; 