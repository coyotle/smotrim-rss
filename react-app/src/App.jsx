import "./App.css";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./home";
import Listen from "./listen";

function App() {
  return (
    <div className="grid grid-cols-6">
      <div></div>
      <div className="col-span-4 w-full flex justify-center items-center">
        <Router>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/listen" element={<Listen />} />
          </Routes>
        </Router>
      </div>
      <div></div>
    </div>
  );
}

export default App;
