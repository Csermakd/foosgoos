import { createBrowserRouter, RouterProvider } from "react-router-dom"
import { Button } from "@/components/ui/button"
import UserCreate from "./pages/UserCreate"
import GamePlay from "./pages/GamePlay"
import CreateGame from "./pages/CreateGame"

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <div className="flex min-h-svh flex-col items-center justify-center">
        <Button>Click me</Button>
      </div>
    ),
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

