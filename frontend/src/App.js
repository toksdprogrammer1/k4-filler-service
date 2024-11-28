import React, { useState } from 'react';
import { 
  Container, 
  Paper, 
  TextField, 
  Button, 
  Typography,
  CircularProgress,
  Snackbar,
  Alert
} from '@mui/material';

function App() {
  const [file, setFile] = useState(null);
  const [formData, setFormData] = useState({
    taxYear: new Date().getFullYear() - 1,
    brokerName: '',
    accountNumber: '',
    taxpayerName: '',
    taxpayerSin: ''
  });
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    const formDataToSend = new FormData();
    formDataToSend.append('file', file);
    formDataToSend.append('tax_year', formData.taxYear);
    formDataToSend.append('broker_name', formData.brokerName);
    formDataToSend.append('account_number', formData.accountNumber);
    formDataToSend.append('taxpayer_name', formData.taxpayerName);
    formDataToSend.append('taxpayer_sin', formData.taxpayerSin);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 300000); // 5-minute timeout

      const response = await fetch('http://localhost:8000/api/process-statement', {
        method: 'POST',
        body: formDataToSend,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Server error');
      }

      const result = await response.json();
      if (result.pdf_content) {
        // Convert base64 string to binary
        const binaryString = window.atob(result.pdf_content);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        
        // Create blob and download
        const blob = new Blob([bytes], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'filled_k4.pdf');
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        
        setNotification({
          open: true,
          message: 'K4 form processed successfully!',
          severity: 'success'
        });
      }
    } catch (error) {
      console.error('Error:', error);
      setNotification({
        open: true,
        message: error.name === 'AbortError' 
          ? 'Request timed out. Please try again.' 
          : `Error: ${error.message}`,
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  return (
    <Container maxWidth="md">
      <Paper elevation={3} style={{ padding: '2rem', marginTop: '2rem' }}>
        <Typography variant="h4" gutterBottom>
          K4 Filler Service
        </Typography>
        
        <form onSubmit={handleSubmit}>
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files?.[0])}
            style={{ marginBottom: '1rem' }}
          />
          
          <TextField
            fullWidth
            label="Tax Year"
            type="number"
            value={formData.taxYear}
            onChange={(e) => setFormData({...formData, taxYear: parseInt(e.target.value)})}
            margin="normal"
          />
          
          <TextField
            fullWidth
            label="Broker Name"
            value={formData.brokerName}
            onChange={(e) => setFormData({...formData, brokerName: e.target.value})}
            margin="normal"
          />
          
          <TextField
            fullWidth
            label="Account Number"
            value={formData.accountNumber}
            onChange={(e) => setFormData({...formData, accountNumber: e.target.value})}
            margin="normal"
          />
          
          <TextField
            fullWidth
            label="Taxpayer Name"
            value={formData.taxpayerName}
            onChange={(e) => setFormData({...formData, taxpayerName: e.target.value})}
            margin="normal"
          />
          
          <TextField
            fullWidth
            label="Taxpayer SIN"
            value={formData.taxpayerSin}
            onChange={(e) => setFormData({...formData, taxpayerSin: e.target.value})}
            margin="normal"
          />
          
          <Button 
            variant="contained" 
            color="primary" 
            type="submit"
            disabled={loading || !file}
            style={{ marginTop: '1rem' }}
          >
            {loading ? (
              <>
                <CircularProgress size={24} style={{ marginRight: '10px' }} />
                Processing...
              </>
            ) : 'Process Statement'}
          </Button>
        </form>

        <Snackbar 
          open={notification.open} 
          autoHideDuration={6000} 
          onClose={handleCloseNotification}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert 
            onClose={handleCloseNotification} 
            severity={notification.severity}
            sx={{ width: '100%' }}
          >
            {notification.message}
          </Alert>
        </Snackbar>
      </Paper>
    </Container>
  );
}

export default App; 