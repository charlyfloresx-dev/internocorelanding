namespace Interno.Outset
{
    public static class DbInitilizer
    {
        public static void Initializer(Interno.Outset.Models.OutsetContext context)
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
                Interno.HumanResource.Models.Catalog.Shift shift = new HumanResource.Models.Catalog.Shift{ Code="T1",Start = TimeSpan.Parse("07:00"),End = TimeSpan.Parse("19:00"),Name="Primer Turno"};
                context.Shift.Add(shift);
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
                var init = TimeSpan.Parse("09:00");
                var end = TimeSpan.Parse("9:30");
                
                for (int i = 1; i < 4; i++)
                {
                    Interno.HumanResource.Models.Catalog.Break break1 = new Interno.HumanResource.Models.Catalog.Break { Code = "D0"+i,Start = init,End = end, Type = tipo, Duration = init- end };
                    context.Add(break1);
                    init += TimeSpan.Parse("00:30:00");
                    end += TimeSpan.Parse("00:30:00");
                    Console.WriteLine(init); Console.WriteLine(end);
                }
                var init2 = TimeSpan.Parse("13:00");
                var end2 = TimeSpan.Parse("13:30");
                for (int i = 1; i < 4; i++)
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
                    new Interno.Production.Models.Resource{ Code = "L01",Name = "Cart 1",Type = type, BreakGroupId = 1},
                    new Interno.Production.Models.Resource{ Code = "L02",Name = "Cart 2",Type = type, BreakGroupId = 1},
                    new Interno.Production.Models.Resource{ Code = "L03",Name = "Cart 3",Type = type, BreakGroupId = 1},
                    new Interno.Production.Models.Resource{ Code = "L04",Name = "Cart 4",Type = type, BreakGroupId = 2},
                    new Interno.Production.Models.Resource{ Code = "L05",Name = "Cart 5",Type = type, BreakGroupId = 2},
                    new Interno.Production.Models.Resource{ Code = "L06",Name = "Cart 6",Type = type, BreakGroupId = 2},
                };
                foreach (var item in res) context.Resource.Add(item);
            }
            Console.WriteLine(context.SaveChanges());
        }
    }    
}