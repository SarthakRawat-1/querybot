import { Link } from 'react-router-dom';
import { LayoutDashboard, LayoutGrid, Database } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

/** Navigation menu for the shared public workspace. */
const UserMenu = () => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="bg-primary/10 text-primary hover:bg-primary/20 rounded-full text-xs font-semibold"
          aria-label="Account menu"
        >
          <Database className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="text-foreground font-normal">
          <p className="truncate text-sm font-medium">Public workspace</p>
          <p className="text-muted-foreground truncate text-xs">Anyone can use this workspace</p>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        <DropdownMenuItem asChild>
          <Link to="/">
            <LayoutGrid className="h-4 w-4" />
            Playground
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link to="/dashboards">
            <LayoutDashboard className="h-4 w-4" />
            Dashboards
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default UserMenu;
