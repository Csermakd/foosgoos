import { createBrowserRouter, RouterProvider } from "react-router-dom"
import UserCreate from "./pages/UserCreate"
import GamePlay from "./pages/GamePlay"
import CreateGame from "./pages/CreateGame"
import Home from "./components/Home"
import ViewUser from "./pages/ViewUser"
import Leaderboards from "./pages/Leaderboards"
import Stats from "./pages/Stats"

const router = createBrowserRouter([
  {
    path: "/",
    element: <Home />,
  },
  {
    path: "/game-play",
    element: <GamePlay />,
  },
  {
    path: "/create-game",
    element: <CreateGame />,
  },
  {
    path: "/create-user",
    element: <UserCreate />,
  },
  {
    path: "/view-user",
    element: <ViewUser />,
  },
  {
    path: "/leaderboards",
    element: <Leaderboards />,
  },
  {
    path: "/statistics",
    element: <Stats />,
  }
])

function App() {
  return <RouterProvider router={router} />
}

export default App

