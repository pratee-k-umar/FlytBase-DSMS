import { Monitor } from "lucide-react";
import { useEffect, useState } from "react";

export default function DeviceRestriction({
    children,
}: {
    children: React.ReactNode;
}) {
    const [isPortraitMobileOrTablet, setIsPortraitMobileOrTablet] =
        useState(false);

    useEffect(() => {
        const checkDevice = () => {
            const width = window.innerWidth;
            const height = window.innerHeight;
            const isPortrait = height > width;
            const isMobileOrTablet = width < 1024; // Below 1024px is considered mobile/tablet

            // Show restriction only if it's mobile/tablet AND in portrait mode
            setIsPortraitMobileOrTablet(isMobileOrTablet && isPortrait);
        };

        checkDevice();
        window.addEventListener("resize", checkDevice);
        window.addEventListener("orientationchange", checkDevice);

        return () => {
            window.removeEventListener("resize", checkDevice);
            window.removeEventListener("orientationchange", checkDevice);
        };
    }, []);

    if (isPortraitMobileOrTablet) {
        return (
            <div className="fixed inset-0 bg-background flex items-center justify-center p-6">
                <div className="text-center max-w-md">
                    <div className="mb-6 flex justify-center">
                        <Monitor className="w-20 h-20 text-primary" />
                    </div>
                    <h1 className="text-2xl font-bold text-foreground mb-4">
                        Desktop View Required
                    </h1>
                    <p className="text-muted-foreground mb-6">
                        This application is optimized for desktop and landscape
                        viewing. Please open it on a desktop computer or rotate
                        your device to landscape mode for the best experience.
                    </p>
                    <div className="flex flex-col gap-2 text-sm text-muted-foreground">
                        <p>Use a desktop or laptop</p>
                        <p>Rotate your device to landscape</p>
                    </div>
                </div>
            </div>
        );
    }

    return <>{children}</>;
}
