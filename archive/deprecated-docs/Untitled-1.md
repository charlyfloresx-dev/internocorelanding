
--- ZPL Printing and Socket Management (Interno.DJO) ---
File: src/Interno.DJO/Services/Printer.cs

Description: This file contains the `IPrinterService` interface and its implementation `EmailService` (Note: the class is named EmailService but implements IPrinterService and handles printing). The `Send` method within this class is responsible for sending ZPL (Zebra Programming Language) strings to a printer over a TCP/IP network connection.

Extracted Code (Send method):
```csharp
public void Send(string ipAddress, int port, string ZPLString)
{
    try
    {
        // Open connection
        System.Net.Sockets.TcpClient client = new System.Net.Sockets.TcpClient();
        client.Connect(ipAddress, port);

        // Write ZPL String to connection
        System.IO.StreamWriter writer = new System.IO.StreamWriter(client.GetStream());
        writer.Write(ZPLString);
        writer.Flush();

        // Close Connection
        writer.Close();
        client.Close();
    }
    catch (Exception ex)
    {
        // Catch Exception
    }
}
```

ZPL String Construction Logic (commented out example in file):
```csharp
/*
string ZPLString =
"^XA" +
"^FO50,50" +
"^A0N50,50" +
"^FDHello, World!^FS" +
"^XZ";
*/
```
This commented-out section shows how ZPL commands are constructed, using `^XA` to start and `^XZ` to end the print job, along with various field commands (`^FO`, `^A0`, `^FD`, `^FS`).
