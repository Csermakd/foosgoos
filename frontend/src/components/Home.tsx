import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/Card";
import { useDispatch, useSelector } from "react-redux";
import { type AppDispatch, type RootState } from "@/store";
import { fetchAllUsers } from "@/features/user/userSlice";

const Home = () => {
  const navigate = useNavigate();
  const dispatch: AppDispatch = useDispatch();

  const userStatus = useSelector((state: RootState) => state.users.status);

  useEffect(() => {
    if (userStatus === 'idle') {
      dispatch(fetchAllUsers());
    }
  }, [dispatch, userStatus]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-[#FEFADC]">
      <Card className="w-4/5 max-w-3xl p-8 flex flex-col justify-between gap-8">
        {/* Top half: 3 buttons in a row */}
        <div className="flex flex-row gap-4">
          <Button className="flex-1" onClick={() => navigate("/create-game")}>
            Start Game
          </Button>
          <Button className="flex-1" onClick={() => navigate("/create-user")}>
            Create User
          </Button>
          <Button className="flex-1" onClick={() => navigate("/view-user")}>
            View User
          </Button>
        </div>
        {/* Bottom half: 2 buttons side by side */}
        <div className="flex gap-4">
          <Button className="w-1/2" onClick={() => navigate("/leaderboards")}>
            Leaderboards
          </Button>
          <Button className="w-1/2" onClick={() => navigate("/statistics")}>
            Statistics
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default Home;

