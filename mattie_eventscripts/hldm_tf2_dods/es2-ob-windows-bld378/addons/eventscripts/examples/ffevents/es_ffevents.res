//=========== (C) Copyright 2005 Mattie Casper All rights reserved. ===========
//
// Events triggered by ffevents mod


// No spaces in event names, max length 32
// All strings are case sensitive
// total game event byte length must be < 1024
//
// valid data key types are:
//   none   : value is not networked
//   string : a zero terminated string
//   bool   : unsigned int, 1 bit
//   byte   : unsigned int, 8 bit
//   short  : signed int, 16 bit
//   long   : signed int, 32 bit
//   float  : float, 32 bit

"ffevents"
{
	"teammate_hurt"
	{
		"userid"        "short"         // wounded player
		"attacker"      "string"        // attacking teammate
	}
	"teammate_kill"
	{
		"userid"        "short"         // killed player
		"attacker"      "string"        // attacking teammate
	}
}
