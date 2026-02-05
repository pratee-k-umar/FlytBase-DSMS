import { Link, Outlet, useLocation } from "react-router-dom";

export default function Layout() {
    const location = useLocation();

    const navigation = [
        { name: "Bases", href: "/bases" },
        { name: "Drones", href: "/drones" },
        { name: "Missions", href: "/missions" },
        { name: "Mission Planner", href: "/mission/planner" },
        { name: "Live Monitor", href: "/mission/monitor" },
        { name: "Analytics", href: "/analytics" },
    ];

    return (
        <div className="min-h-screen bg-background">
            {/* Sidebar */}
            <div className="fixed inset-y-0 left-0 w-64 bg-card border-r">
                <div className="flex flex-col h-full">
                    {/* Logo */}
                    <div className="px-6 py-4 border-b">
                        <h1 className="text-2xl font-bold text-foreground">
                            DSMS
                        </h1>
                        <p className="text-sm text-muted-foreground">
                            Drone Survey Management
                        </p>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-4 py-4 space-y-1">
                        {navigation.map((item) => {
                            const isActive = location.pathname === item.href;
                            return (
                                <Link
                                    key={item.name}
                                    to={item.href}
                                    className={`
                    flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors
                    ${
                        isActive
                            ? "bg-accent text-accent-foreground"
                            : "text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground"
                    }
                  `}
                                >
                                    {item.name}
                                </Link>
                            );
                        })}
                    </nav>

                    {/* Footer */}
                    <div className="px-6 py-4 border-t border-gray-200">
                        <p className="text-xs text-gray-500">
                            Built by Prateek
                        </p>
                    </div>
                </div>
            </div>

            {/* Main content */}
            <div className="pl-64">
                <main className="min-h-screen">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
