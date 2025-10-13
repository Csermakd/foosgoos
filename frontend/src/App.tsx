import { createBrowserRouter, RouterProvider } from "react-router-dom"
import { Button } from "@/components/ui/button"
import UserCreate from "./pages/UserCreate"
import GamePlay from "./pages/GamePlay"
import CreateGame from "./pages/CreateGame"
import Home from "./components/Home"

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
])

function App() {
  return <RouterProvider router={router} />
}

export default App

