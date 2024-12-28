// pages/login.tsx
'use client'

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '../../utils/axios';

export default function Login() {
  const router = useRouter();
  const [mobile, setMobile] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await api.post('/login', { mobile, password });
      const { token } = response.data;

      // Store token in localStorage
      localStorage.setItem('auth_token', token);

      // Redirect to home page upon success
      router.push('/home');
    } catch (err) {
      console.log(err);
      setError('Invalid credentials');
    }
  };

  return (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleLogin}>
        <input
          type="text"
          placeholder="Mobile"
          value={mobile}
          onChange={(e) => setMobile(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p>{error}</p>}
        <button type="submit">Login</button>
      </form>
    </div>
  );
};
