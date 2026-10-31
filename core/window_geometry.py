"""Clamp a pet window to a chosen screen's available logical-pixel rectangle."""


def recover_geometry(x,y,width,height,area):
    left,top,available_width,available_height = area
    scale = min(1.,max(1,available_width)/max(1,width),max(1,available_height)/max(1,height))
    width,height = max(1,int(width*scale)),max(1,int(height*scale))
    return (max(left,min(x,left+available_width-width)),
            max(top,min(y,top+available_height-height)),width,height)
