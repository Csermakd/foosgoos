import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import { Button } from "@/components/ui/button"
import UserCreate from "./pages/UserCreate"

function App() {
  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            <div className="flex min-h-svh flex-col items-center justify-center">
              <Button>Click me</Button>
            </div>
          }
        />
        <Route path="/create-user" element={<UserCreate />} />
      </Routes>
    </Router>
  )
}

export default App