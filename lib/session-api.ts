export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

export async function api<T>(path:string, body?:object):Promise<T>{
  let csrf='';
  if(body){
    const res=await fetch('/api/v1/auth/csrf/',{cache:'no-store',credentials:'same-origin'});
    if(!res.ok) throw new Error('Cannot prepare a secure request.');
    csrf=(await res.json()).csrfToken;
  }
  const res=await fetch(`/api/v1${path}`,{method:body?'POST':'GET',credentials:'same-origin',cache:'no-store',
    headers:{Accept:'application/json',...(body?{'Content-Type':'application/json','X-CSRFToken':csrf}:{})},
    ...(body?{body:JSON.stringify(body)}:{})});
  const data=await res.json();
  if(!res.ok) throw new ApiError(typeof data.detail==='string'?data.detail:JSON.stringify(data), res.status);
  return data as T;
}
