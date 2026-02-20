using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using System.Text.Json;
using System.Text.Json.Serialization;

namespace Interno.Production.Data
{
    public static class DbInitilizer
    {
        public static void Initializer(Interno.Production.Models.ProductionContext context)
        {
            if(!context.UM.Any())
            {
                var um = new Interno.Domain.Catalog.UM();
                foreach (Interno.Domain.Catalog.UM u in um.initialList()) context.UM.Add(u); 
            }
            
            if(!context.Partnership.Any())
            {
                Interno.Inventory.Models.Partnership par = new Interno.Inventory.Models.Partnership{ Code="GENERAL",Name="General Customer" };
                context.Partnership.Add(par);
            }
            if(!context.Shift.Any()){
                Interno.HumanResource.Models.Catalog.Shift shift = new HumanResource.Models.Catalog.Shift{ Code="T1",Start = TimeSpan.Parse("06:00"),End = TimeSpan.Parse("16:30"),Name="Primer Turno"};
                context.Shift.Add(shift);
                Interno.HumanResource.Models.Catalog.Shift shift2 = new HumanResource.Models.Catalog.Shift{ Code="T2",Start = TimeSpan.Parse("16:30"),End = TimeSpan.Parse("01:45"),Name="Segundo Turno" };
                context.Shift.Add(shift2);
            }
            if(context.BreakType.Any()){
                Interno.HumanResource.Models.Catalog.BreakType tipo = new Interno.HumanResource.Models.Catalog.BreakType { Name = "Descanzo 1" };
                context.Add(tipo);
                Interno.HumanResource.Models.Catalog.BreakType tipo1 = new Interno.HumanResource.Models.Catalog.BreakType { Name = "Descanzo 2" };
                context.Add(tipo1);
            }
            
             if(!context.Break.Any()){
                    Interno.HumanResource.Models.Catalog.BreakType tipo = new Interno.HumanResource.Models.Catalog.BreakType { Name = "Descanzo 1" };
                    context.Add(tipo);
                    Interno.HumanResource.Models.Catalog.BreakType tipo1 = new Interno.HumanResource.Models.Catalog.BreakType { Name = "Descanzo 2" };
                    context.Add(tipo1);
                    //Desallunos
                    var init = TimeSpan.Parse("07:45");
                    var end = TimeSpan.Parse("8:15");
                    
                    for (int i = 1; i < 5; i++)
                    {
                        Interno.HumanResource.Models.Catalog.Break break1 = new Interno.HumanResource.Models.Catalog.Break { Code = "D0"+i,Start = init,End = end, Type = tipo, Duration = init- end };
                        context.Add(break1);
                        init += TimeSpan.Parse("00:30:00");
                        end += TimeSpan.Parse("00:30:00");
                        Console.WriteLine(init); Console.WriteLine(end);
                    }
                    var init2 = TimeSpan.Parse("11:45");
                    var end2 = TimeSpan.Parse("12:15");
                    for (int i = 1; i < 5; i++)
                    {
                        Interno.HumanResource.Models.Catalog.Break break1 = new Interno.HumanResource.Models.Catalog.Break { Code = "C0"+i,Start = init2,End = end2, Type = tipo1, Duration = init2- end2 };
                        context.Add(break1);
                        init2 += TimeSpan.Parse("00:30:00");
                        end2 += TimeSpan.Parse("00:30:00");
                        Console.WriteLine(init); Console.WriteLine(end);
                    }
             }
            
                if(!context.Resource.Any())
                {
                    Inventory.Models.WarehouseType type = new Inventory.Models.WarehouseType{ Name = "Station"};
                    context.WarehouseType.Add(type);
                    Interno.Production.Models.Resource[] res = {
                        new Interno.Production.Models.Resource{ Code = "L01",Name = "Linea 1",Type = type, BreakGroupId = 1},
                        new Interno.Production.Models.Resource{ Code = "L02",Name = "Linea 2",Type = type, BreakGroupId = 1},
                        new Interno.Production.Models.Resource{ Code = "L03",Name = "Linea 3",Type = type, BreakGroupId = 1},
                        new Interno.Production.Models.Resource{ Code = "L04",Name = "Linea 4",Type = type, BreakGroupId = 2},
                        new Interno.Production.Models.Resource{ Code = "L05",Name = "Linea 5",Type = type, BreakGroupId = 2},
                        new Interno.Production.Models.Resource{ Code = "L06",Name = "Linea 6",Type = type, BreakGroupId = 2},
                        new Interno.Production.Models.Resource{ Code = "L07",Name = "Linea 7",Type = type, BreakGroupId = 3},
                        new Interno.Production.Models.Resource{ Code = "L08",Name = "Linea 8",Type = type, BreakGroupId = 3},
                        new Interno.Production.Models.Resource{ Code = "L09",Name = "Linea 9",Type = type, BreakGroupId = 3},
                        new Interno.Production.Models.Resource{ Code = "L10",Name = "Linea 10",Type = type, BreakGroupId = 3},
                        new Interno.Production.Models.Resource{ Code = "L11",Name = "Linea 11",Type = type, BreakGroupId = 4},
                        new Interno.Production.Models.Resource{ Code = "L12",Name = "Linea 12",Type = type, BreakGroupId = 4},
                        new Interno.Production.Models.Resource{ Code = "L13",Name = "Linea 13",Type = type, BreakGroupId = 4},
                        new Interno.Production.Models.Resource{ Code = "L14",Name = "Linea 14",Type = type, BreakGroupId = 4}
                    };
                    foreach (var item in res) context.Resource.Add(item);
                }
                Console.WriteLine(context.SaveChanges());
        }
    }
}
