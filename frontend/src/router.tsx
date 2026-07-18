import { createBrowserRouter } from 'react-router-dom';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './pages/Dashboard';
import Predict from './pages/Predict';
import FoodLog from './pages/FoodLog';
import Report from './pages/Report';
import Login from './pages/Login';
import Register from './pages/Register';

export const router = createBrowserRouter([
  { path: '/login',    element: <Login /> },
  { path: '/register', element: <Register /> },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      { index: true,          element: <Dashboard /> },
      { path: 'predict',      element: <Predict /> },
      { path: 'food-log',     element: <FoodLog /> },
      { path: 'report',       element: <Report /> },
    ],
  },
]);
